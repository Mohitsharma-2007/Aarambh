import React, { useState, useEffect, useCallback, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import * as d3 from "d3";
import { graphApi, simulationApi } from "../api/ontology";
import GraphPanel from "../components/ontology/GraphPanel";
import { Maximize2, Minimize2, RefreshCw, Layers, Database } from 'lucide-react';

// Types
interface GraphNode {
  uuid: string;
  name: string;
  labels: string[];
  attributes?: Record<string, any>;
  summary?: string;
  created_at?: string;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

interface GraphEdge {
  uuid: string;
  source_node_uuid: string;
  target_node_uuid: string;
  source?: any;
  target?: any;
  fact_type: string;
  name: string;
  fact?: string;
  episodes?: string[];
  created_at?: string;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  node_count?: number;
  edge_count?: number;
}

interface OntologyData {
  entity_types?: Array<{
    name: string;
    description: string;
    attributes?: any[];
    examples?: string[];
  }>;
  edge_types?: Array<{
    name: string;
    description: string;
    source_types?: string[];
    target_types?: string[];
  }>;
  relation_types?: any[];
  analysis_summary?: string;
}

interface ProjectData {
  project_id: string;
  name?: string;
  graph_id?: string;
  ontology?: OntologyData;
  status?: string;
  simulation_requirement?: string;
  error?: string;
  graph_build_task_id?: string;
}

interface BuildProgress {
  progress: number;
  message: string;
}

interface OntologyProgress {
  message: string;
}

interface SelectedItem {
  type: "node" | "edge";
  data: any;
  color?: string;
  entityType?: string;
}

const COLORS = [
  "#FF6B35",
  "#004E89",
  "#7B2D8E",
  "#1A936F",
  "#C5283D",
  "#E9724C",
  "#3498db",
  "#9b59b6",
];

export const OntologyProcess: React.FC = () => {
  const { projectId: routeProjectId } = useParams();
  const navigate = useNavigate();
  const graphContainerRef = useRef<HTMLDivElement>(null);

  // State
  const [currentProjectId, setCurrentProjectId] = useState(
    routeProjectId || "",
  );
  const [projectData, setProjectData] = useState<ProjectData | null>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [currentPhase, setCurrentPhase] = useState(-1);
  const [loading, setLoading] = useState(true);
  const [graphLoading, setGraphLoading] = useState(false);
  const [error, setError] = useState("");
  const [buildProgress, setBuildProgress] = useState<BuildProgress | null>(
    null,
  );
  const [ontologyProgress, setOntologyProgress] =
    useState<OntologyProgress | null>(null);
  const [selectedItem, setSelectedItem] = useState<SelectedItem | null>(null);
  const [isFullScreen, setIsFullScreen] = useState(false);

  // Poll timers
  const pollTimerRef = useRef<NodeJS.Timeout | null>(null);
  const graphPollTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Calculate entity types for legend
  const entityTypes = React.useMemo(() => {
    if (!graphData?.nodes) return [];
    const typeMap: Record<
      string,
      { name: string; count: number; color: string }
    > = {};

    graphData.nodes.forEach((node) => {
      const type =
        node.labels?.find((l) => l !== "Entity" && l !== "Node") || "Entity";
      if (!typeMap[type]) {
        typeMap[type] = {
          name: type,
          count: 0,
          color: COLORS[Object.keys(typeMap).length % COLORS.length],
        };
      }
      typeMap[type].count++;
    });
    return Object.values(typeMap);
  }, [graphData]);

  const getColor = useCallback(
    (type: string) => {
      const found = entityTypes.find((t) => t.name === type);
      return found?.color || "#999";
    },
    [entityTypes],
  );

  // Status computed values
  const statusClass = error
    ? "error"
    : currentPhase >= 2
      ? "completed"
      : "processing";
  const statusText = error
    ? "Build Failed"
    : currentPhase >= 2
      ? "Build Complete"
      : currentPhase === 1
        ? "Building Graph"
        : currentPhase === 0
          ? "Generating Ontology"
          : "Initializing";

  // Initialize
  useEffect(() => {
    if (routeProjectId) {
      if (routeProjectId === "new") {
        handleNewProject();
      } else {
        setCurrentProjectId(routeProjectId);
        loadProject(routeProjectId);
      }
    }
    return () => {
      // Cleanup happens but timers are no longer set
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [routeProjectId]);

  const stopPolling = () => {
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  };

  const stopGraphPolling = () => {
    if (graphPollTimerRef.current) {
      clearInterval(graphPollTimerRef.current);
      graphPollTimerRef.current = null;
    }
  };

  const handleNewProject = async () => {
    const requirement = sessionStorage.getItem("aarambh_requirement") || "";

    if (!requirement) {
      setError("No requirement found. Please return to home and try again.");
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setCurrentPhase(0);
      setOntologyProgress({ message: "Analyzing documents..." });

      const formData = new FormData();
      formData.append("simulation_requirement", requirement);
      formData.append("project_name", `Project ${Date.now()}`);

      const res = await graphApi.generateOntology(formData);

      if (res.data?.success) {
        sessionStorage.removeItem("aarambh_requirement");
        sessionStorage.removeItem("aarambh_files");

        const result = res.data.data;
        setCurrentProjectId(result.project_id);
        setProjectData(result);
        setOntologyProgress(null);

        navigate(`/ontology/process/${result.project_id}`, { replace: true });

        await startBuildGraph(result.project_id);
      } else {
        setError(res.data?.error || "Ontology generation failed");
      }
    } catch (err: any) {
      setError(
        "Project initialization failed: " + (err.message || "Unknown error"),
      );
    } finally {
      setLoading(false);
    }
  };

  const loadProject = async (pid: string) => {
    try {
      setLoading(true);

      // Optionally check project state for redirect (non-fatal if unavailable)
      try {
        const stateRes = await graphApi.getProjectState(pid);
        if (stateRes.data?.success && stateRes.data.data?.redirect_url) {
          // Redirect to the appropriate step
          navigate(stateRes.data.data.redirect_url, { replace: true });
          return;
        }
      } catch {
        // getProjectState endpoint unavailable — continue with normal load
      }

      const res = await graphApi.getProject(pid);

      if (res.data?.success) {
        setProjectData(res.data.data);
        updatePhaseByStatus(res.data.data.status);

        if (
          res.data.data.status === "ontology_generated" &&
          !res.data.data.graph_id
        ) {
          await startBuildGraph(pid);
        }

        if (
          res.data.data.status === "graph_building" &&
          res.data.data.graph_build_task_id
        ) {
          setCurrentPhase(1);
          startPollingTask(res.data.data.graph_build_task_id, pid);
        }

        if (
          res.data.data.status === "graph_completed" &&
          res.data.data.graph_id
        ) {
          setCurrentPhase(2);
          await loadGraph(res.data.data.graph_id);
        }
      } else {
        setError(res.data?.error || "Failed to load project");
      }
    } catch (err: any) {
      setError("Failed to load project: " + (err.message || "Unknown error"));
    } finally {
      setLoading(false);
    }
  };

  const updatePhaseByStatus = (status?: string) => {
    switch (status) {
      case "created":
      case "ontology_generated":
        setCurrentPhase(0);
        break;
      case "graph_building":
        setCurrentPhase(1);
        break;
      case "graph_completed":
        setCurrentPhase(2);
        break;
      case "failed":
        setError(projectData?.error || "Processing failed");
        break;
    }
  };

  const startBuildGraph = async (pid: string) => {
    try {
      setCurrentPhase(1);
      setBuildProgress({ progress: 0, message: "Starting graph build..." });

      const res = await graphApi.buildGraph({ project_id: pid });

      if (res.data?.success && res.data.data?.task_id) {
        startPollingTask(res.data.data.task_id, pid);
        startGraphPolling(pid);
      } else {
        setError(res.data?.error || "Failed to start graph build");
        setBuildProgress(null);
      }
    } catch (err: any) {
      // Handle "already building" 400 response — resume polling instead of erroring
      const errData = err?.response?.data;
      if (err?.response?.status === 400 && errData?.task_id) {
        console.log("[Build] Already in progress, resuming poll:", errData.task_id);
        startPollingTask(errData.task_id, pid);
        startGraphPolling(pid);
        return;
      }
      setError(
        "Failed to start graph build: " + (err.message || "Unknown error"),
      );
      setBuildProgress(null);
    }
  };

  const startPollingTask = (taskId: string, pid: string) => {
    pollTaskStatus(taskId, pid);
    pollTimerRef.current = setInterval(() => pollTaskStatus(taskId, pid), 2000);
  };

  const pollTaskStatus = async (taskId: string, pid: string) => {
    try {
      const res = await graphApi.getTaskStatus(taskId);

      if (res.data?.success) {
        const task = res.data.data;
        setBuildProgress({
          progress: task.progress || 0,
          message: task.message || "Processing...",
        });

        if (task.status === "completed") {
          stopPolling();
          stopGraphPolling();
          setCurrentPhase(2);

          const projectRes = await graphApi.getProject(pid);
          if (projectRes.data?.success) {
            setProjectData(projectRes.data.data);
            if (projectRes.data.data.graph_id) {
              await loadGraph(projectRes.data.data.graph_id);
            }
          }
          setBuildProgress(null);
        } else if (task.status === "failed") {
          stopPolling();
          stopGraphPolling();
          setError("Graph build failed: " + (task.error || "Unknown error"));
          setBuildProgress(null);
        }
      }
    } catch (err) {
      // Continue polling
    }
  };

  const startGraphPolling = (pid: string) => {
    fetchGraphData(pid);
    graphPollTimerRef.current = setInterval(() => fetchGraphData(pid), 10000);
  };

  const fetchGraphData = async (pid: string) => {
    try {
      const projectRes = await graphApi.getProject(pid);
      if (projectRes.data?.success && projectRes.data.data.graph_id) {
        const graphRes = await graphApi.getGraphData(
          projectRes.data.data.graph_id,
        );
        if (graphRes.data?.success && graphRes.data.data) {
          const newData = graphRes.data.data;
          const oldCount =
            graphData?.node_count || graphData?.nodes?.length || 0;
          const newCount = newData.node_count || newData.nodes?.length || 0;

          if (newCount !== oldCount || !graphData) {
            setGraphData(newData);
          }
        }
      }
    } catch (err) {
      // Ignore
    }
  };

  const loadGraph = async (graphId: string) => {
    try {
      setGraphLoading(true);
      setError("");
      const res = await graphApi.getGraphData(graphId);
      if (res.data?.success) {
        setGraphData(res.data.data);
      } else {
        setError(res.data?.error || "Failed to load graph data");
      }
    } catch (err: any) {
      setError("Failed to load graph: " + (err.message || "Unknown error"));
    } finally {
      setGraphLoading(false);
    }
  };

  const refreshGraph = async () => {
    if (!projectData?.graph_id) return;
    setGraphLoading(true);
    await loadGraph(projectData.graph_id);
    setGraphLoading(false);
  };

  const toggleFullScreen = () => {
    setIsFullScreen(!isFullScreen);
  };

  // Render logic removed in favor of GraphPanel component

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return "-";
    try {
      return new Date(dateStr).toLocaleString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return dateStr;
    }
  };

  const getPhaseStatusClass = (phase: number) => {
    if (currentPhase > phase) return "completed";
    if (currentPhase === phase) return "active";
    return "pending";
  };

  const getPhaseStatusText = (phase: number) => {
    if (currentPhase > phase) return "Completed";
    if (currentPhase === phase) {
      if (phase === 1 && buildProgress) {
        return `${buildProgress.progress}%`;
      }
      return "Processing";
    }
    return "Waiting";
  };

  const goHome = () => navigate("/ontology");

  const goToNextStep = async () => {
    if (!projectData?.project_id || !projectData?.graph_id) return;

    try {
      const res = await simulationApi.create({
        project_id: projectData.project_id,
        graph_id: projectData.graph_id,
        enable_twitter: true,
        enable_reddit: true,
        max_rounds: 10,
      });

      if (res.data?.success && res.data.data?.simulation_id) {
        navigate(`/ontology/simulation/${res.data.data.simulation_id}`);
      }
    } catch (err) {
      alert("Failed to create simulation");
    }
  };

  return (
    <div className="h-screen bg-[#0F1117] text-[#F5F0EB] font-['Inter',sans-serif] flex flex-col overflow-hidden">
      {/* Navbar */}
      <nav className="h-[60px] bg-[#161822] border-b border-[rgba(250,212,192,0.12)] flex items-center justify-between px-8 shrink-0 text-white">
        <div
          className="font-extrabold text-xl tracking-wider cursor-pointer text-[#FAD4C0]"
          onClick={goHome}
        >
          AARAMBH
        </div>

        <div className="flex items-center gap-6">
          <div className="flex items-center gap-4">
            <span className="text-[10px] font-mono bg-[#FAD4C0] text-[#111827] px-2 py-0.5 font-bold rounded uppercase">Step 01</span>
            <span className="text-xs font-mono tracking-widest text-[#A8A3B3] uppercase font-bold">Graph Construction</span>
          </div>

          <div className="h-4 w-px bg-white/10" />

          <div className="flex items-center gap-3">
            <span
              className={`w-2 h-2 rounded-full ${statusClass === "error"
                ? "bg-red-500 animate-pulse"
                : statusClass === "completed"
                  ? "bg-[#16A34A]"
                  : "bg-[#FAD4C0] animate-pulse shadow-[0_0_8px_rgba(250,212,192,0.4)]"
                }`}
            />
            <span className="text-[10px] font-mono font-bold uppercase tracking-widest text-white">{statusText}</span>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Graph */}
        <div
          className={`flex-1 flex flex-col border-r border-[rgba(250,212,192,0.06)] ${isFullScreen ? "fixed inset-0 z-50 bg-[#0F1117]" : "bg-[#0F1117]"}`}
        >
          {/* Panel Header */}
          <div className="h-14 border-b border-white/5 flex items-center justify-between px-6 shrink-0 bg-[#161822]">
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 bg-[#FAD4C0] rotate-45" />
              <span className="text-[11px] font-mono font-bold tracking-widest text-white uppercase italic">
                Neural_Knowledge_Matrix
              </span>
            </div>
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-4 text-[10px] font-mono text-[#A8A3B3]">
                {graphData && (
                  <>
                    <div className="flex items-baseline gap-1">
                      <span className="text-white">{graphData.node_count || graphData.nodes?.length || 0}</span>
                      <span className="opacity-50">NODES</span>
                    </div>
                    <div className="w-1 h-1 bg-white/20 rounded-full" />
                    <div className="flex items-baseline gap-1">
                      <span className="text-white">{graphData.edge_count || graphData.edges?.length || 0}</span>
                      <span className="opacity-50">EDGES</span>
                    </div>
                  </>
                )}
              </div>

              <div className="h-4 w-px bg-white/10" />

              <div className="flex items-center gap-2">
                <button
                  onClick={() => currentProjectId && startBuildGraph(currentProjectId)}
                  className="px-4 py-1.5 bg-[#FAD4C0]/5 border border-[#FAD4C0]/20 text-[#FAD4C0] text-[9px] font-mono font-bold uppercase rounded hover:bg-[#FAD4C0] hover:text-[#111827] transition-all"
                >
                  Force_Rebuild
                </button>
              </div>
            </div>
          </div>

          {/* Graph Container */}
          <div className="flex-1 relative overflow-hidden bg-[#07080C]">
            <GraphPanel
              graphData={graphData}
              loading={graphLoading}
              currentPhase={currentPhase}
              onRefresh={refreshGraph}
              onToggleMaximize={toggleFullScreen}
            />
          </div>
          {/* Detail Panel */}
          {selectedItem && (
            <div className="absolute top-6 left-6 right-6 bottom-6 bg-[#161822]/95 border border-[rgba(250,212,192,0.15)] shadow-[0_20px_50px_rgba(0,0,0,0.5)] z-10 overflow-auto rounded-2xl backdrop-blur-md">
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b border-white/5 bg-[#FAD4C0]/5">
                <div className="flex items-center gap-4">
                  {selectedItem.type === "node" && selectedItem.color && (
                    <span
                      className="px-3 py-1 text-[9px] font-mono font-black text-black uppercase rounded tracking-widest"
                      style={{ background: selectedItem.color || '#FAD4C0' }}
                    >
                      {selectedItem.entityType}
                    </span>
                  )}
                  <span className="font-mono text-xs font-bold uppercase tracking-[0.2em] text-white">
                    {selectedItem.type === "node"
                      ? "Entity_Registry"
                      : "Relationship_Vector"}
                  </span>
                </div>
                <button
                  onClick={() => setSelectedItem(null)}
                  className="w-10 h-10 flex items-center justify-center text-[#A8A3B3] hover:text-white hover:bg-white/5 rounded-xl transition-all"
                >
                  ×
                </button>
              </div>

              {/* Content */}
              <div className="p-4 text-sm">
                {selectedItem.type === "node" ? (
                  <>
                    <div className="mb-3">
                      <span className="text-gray-500 text-xs uppercase">
                        Name
                      </span>
                      <div className="font-semibold">
                        {selectedItem.data.name}
                      </div>
                    </div>
                    <div className="mb-3">
                      <span className="text-gray-500 text-xs uppercase">
                        UUID
                      </span>
                      <div className="font-mono text-xs text-gray-600">
                        {selectedItem.data.uuid}
                      </div>
                    </div>
                    {selectedItem.data.created_at && (
                      <div className="mb-3">
                        <span className="text-gray-500 text-xs uppercase">
                          Created
                        </span>
                        <div>{formatDate(selectedItem.data.created_at)}</div>
                      </div>
                    )}
                    {selectedItem.data.attributes &&
                      Object.keys(selectedItem.data.attributes).length >
                      0 && (
                        <div className="mb-3">
                          <span className="text-gray-500 text-xs uppercase block mb-1">
                            Properties
                          </span>
                          <div className="bg-gray-50 p-2 rounded text-xs space-y-1">
                            {Object.entries(selectedItem.data.attributes).map(
                              ([key, val]) => (
                                <div key={key} className="flex gap-2">
                                  <span className="font-medium">{key}:</span>
                                  <span className="text-gray-600">
                                    {String(val)}
                                  </span>
                                </div>
                              ),
                            )}
                          </div>
                        </div>
                      )}
                    {selectedItem.data.summary && (
                      <div className="mb-3">
                        <span className="text-gray-500 text-xs uppercase block mb-1">
                          Summary
                        </span>
                        <p className="text-gray-700 bg-gray-50 p-2 rounded">
                          {selectedItem.data.summary}
                        </p>
                      </div>
                    )}
                    {selectedItem.data.labels &&
                      selectedItem.data.labels.length > 0 && (
                        <div>
                          <span className="text-gray-500 text-xs uppercase block mb-1">
                            Labels
                          </span>
                          <div className="flex flex-wrap gap-1">
                            {selectedItem.data.labels.map((label: string) => (
                              <span
                                key={label}
                                className="px-2 py-0.5 bg-gray-100 text-xs rounded"
                              >
                                {label}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                  </>
                ) : (
                  <>
                    <div className="mb-4 p-2 bg-gray-50 rounded text-xs font-mono">
                      {selectedItem.data.source_name ||
                        selectedItem.data.source_node_name}{" "}
                      &#8594;{" "}
                      {selectedItem.data.name ||
                        selectedItem.data.fact_type ||
                        "RELATED_TO"}{" "}
                      &#8594;{" "}
                      {selectedItem.data.target_name ||
                        selectedItem.data.target_node_name}
                    </div>
                    <div className="mb-3">
                      <span className="text-gray-500 text-xs uppercase">
                        UUID
                      </span>
                      <div className="font-mono text-xs text-gray-600">
                        {selectedItem.data.uuid}
                      </div>
                    </div>
                    <div className="mb-3">
                      <span className="text-gray-500 text-xs uppercase">
                        Type
                      </span>
                      <div>{selectedItem.data.fact_type || "Unknown"}</div>
                    </div>
                    {selectedItem.data.fact && (
                      <div className="mb-3">
                        <span className="text-gray-500 text-xs uppercase block mb-1">
                          Fact
                        </span>
                        <p className="text-gray-700 bg-gray-50 p-2 rounded">
                          {selectedItem.data.fact}
                        </p>
                      </div>
                    )}
                    {selectedItem.data.episodes &&
                      selectedItem.data.episodes.length > 0 && (
                        <div>
                          <span className="text-gray-500 text-xs uppercase block mb-1">
                            Episodes
                          </span>
                          <div className="flex flex-wrap gap-1">
                            {selectedItem.data.episodes.map((ep: string) => (
                              <span
                                key={ep}
                                className="px-2 py-0.5 bg-gray-100 text-xs font-mono rounded"
                              >
                                {ep}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                  </>
                )}
              </div>
            </div>
          )}

          {/* Loading / Empty States */}
          {!graphData && !graphLoading && currentPhase < 1 && (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-gray-400">
              <svg viewBox="0 0 100 100" className="w-24 h-24 mb-4">
                <circle
                  cx="50"
                  cy="20"
                  r="8"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                />
                <circle
                  cx="20"
                  cy="60"
                  r="8"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                />
                <circle
                  cx="80"
                  cy="60"
                  r="8"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                />
                <circle
                  cx="50"
                  cy="80"
                  r="8"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                />
                <line
                  x1="50"
                  y1="28"
                  x2="25"
                  y2="54"
                  stroke="currentColor"
                  strokeWidth="1"
                />
                <line
                  x1="50"
                  y1="28"
                  x2="75"
                  y2="54"
                  stroke="currentColor"
                  strokeWidth="1"
                />
                <line
                  x1="28"
                  y1="60"
                  x2="72"
                  y2="60"
                  stroke="currentColor"
                  strokeWidth="1"
                  strokeDasharray="4"
                />
                <line
                  x1="50"
                  y1="72"
                  x2="26"
                  y2="66"
                  stroke="currentColor"
                  strokeWidth="1"
                />
                <line
                  x1="50"
                  y1="72"
                  x2="74"
                  y2="66"
                  stroke="currentColor"
                  strokeWidth="1"
                />
              </svg>
              <p className="text-sm font-medium">
                Waiting for ontology generation
              </p>
              <p className="text-xs mt-1">
                Graph will auto-build after ontology is generated
              </p>
            </div>
          )}

          {graphLoading && (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-gray-400">
              <div className="flex gap-2 mb-4">
                <div className="w-3 h-3 rounded-full bg-gray-400 animate-bounce" />
                <div className="w-3 h-3 rounded-full bg-gray-400 animate-bounce [animation-delay:0.1s]" />
                <div className="w-3 h-3 rounded-full bg-gray-400 animate-bounce [animation-delay:0.2s]" />
              </div>
              <p className="text-sm">Loading graph data...</p>
            </div>
          )}

          {currentPhase === 1 && !graphData && (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-gray-400">
              <div className="flex gap-2 mb-4">
                <div className="w-3 h-3 rounded-full bg-amber-500 animate-bounce" />
                <div className="w-3 h-3 rounded-full bg-amber-500 animate-bounce [animation-delay:0.1s]" />
                <div className="w-3 h-3 rounded-full bg-amber-500 animate-bounce [animation-delay:0.2s]" />
              </div>
              <p className="text-sm">Building graph...</p>
              <p className="text-xs mt-1">Data will appear soon...</p>
            </div>
          )}

          {error && (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-red-500">
              <span className="text-3xl mb-2">&#9888;</span>
              <p className="text-sm">{error}</p>
            </div>
          )}
        </div>

        {/* Legend */}
        {graphData && entityTypes.length > 0 && (
          <div className="absolute bottom-4 left-4 bg-white/95 border border-gray-200 rounded-lg p-3 shadow-sm max-w-xs">
            <div className="text-[11px] font-semibold text-pink-600 uppercase tracking-wide mb-2">
              Entity Types
            </div>
            <div className="space-y-1.5">
              {entityTypes.map((type) => (
                <div
                  key={type.name}
                  className="flex items-center gap-2 text-xs"
                >
                  <span
                    className="w-2.5 h-2.5 rounded-full shrink-0"
                    style={{ background: type.color }}
                  />
                  <span className="text-gray-600">{type.name}</span>
                  <span className="text-gray-400 ml-auto">{type.count}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Right Panel - Mission Control */}
      {!isFullScreen && (
        <div className="w-[450px] flex flex-col border-l border-white/5 bg-[#0F1117] shrink-0 overflow-hidden shadow-2xl">
          {/* Panel Header */}
          <div className="h-14 border-b border-white/5 flex items-center px-8 bg-[#161822] shrink-0">
            <span className="text-[10px] font-mono font-black text-white uppercase tracking-widest italic">MISSION_CONTROL_CONSOLE</span>
          </div>

          {/* Content Area */}
          <div className="flex-1 overflow-y-auto p-10 space-y-12 scrollbar-thin scrollbar-thumb-white/5">
            {/* Phase Matrix */}
            <section>
              <div className="flex items-center gap-3 mb-10">
                <div className="w-2 h-2 bg-[#FAD4C0] rounded-full shadow-[0_0_8px_rgba(250,212,192,0.4)]" />
                <h3 className="text-xs font-bold text-white uppercase tracking-[0.2em]">Sequence_Alignment</h3>
              </div>

              <div className="space-y-10">
                {[
                  { id: 0, title: "Ontology Construction", desc: "Extracting semantic reality vectors from provided source arrays." },
                  { id: 1, title: "Graph Synthesis", desc: "Constructing multidimensional relationship matrices." },
                  { id: 2, title: "Ready for Simulation", desc: "Neural engine aligned. Ready for parallel execution." }
                ].map((phase) => (
                  <div key={phase.id} className="relative pl-10">
                    {/* Vertical line connector */}
                    {phase.id < 2 && <div className="absolute left-[7px] top-6 bottom-[-40px] w-px bg-white/10" />}

                    <div className={`absolute left-0 top-1 w-4 h-4 rounded-full border-2 transition-all flex items-center justify-center ${currentPhase > phase.id ? "bg-[#16A34A] border-[#16A34A] shadow-[0_0_10px_rgba(22,163,74,0.3)]" :
                      currentPhase === phase.id ? "bg-[#FAD4C0] border-[#FAD4C0] shadow-[0_0_10px_rgba(250,212,192,0.4)]" :
                        "bg-transparent border-white/10"
                      }`}>
                      {currentPhase > phase.id && <span className="text-white text-[8px] font-bold italic">✓</span>}
                      {currentPhase === phase.id && <div className="w-1.5 h-1.5 bg-[#111] rounded-full animate-pulse" />}
                    </div>

                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className={`text-[11px] font-bold uppercase tracking-widest ${currentPhase >= phase.id ? "text-white" : "text-[#A8A3B3]/30"
                          }`}>
                          {phase.title}
                        </span>
                        <span className={`text-[9px] font-mono font-black px-2 py-0.5 border rounded-sm transition-colors ${currentPhase > phase.id ? "border-[#16A34A]/30 text-[#16A34A] bg-[#16A34A]/5" :
                          currentPhase === phase.id ? "border-[#FAD4C0]/30 text-[#FAD4C0] bg-[#FAD4C0]/5" :
                            "border-white/5 text-[#A8A3B3]/20"
                          }`}>
                          {getPhaseStatusText(phase.id)}
                        </span>
                      </div>
                      <p className={`text-[10px] leading-relaxed transition-opacity ${currentPhase >= phase.id ? "text-[#A8A3B3]" : "text-[#A8A3B3]/20"
                        }`}>
                        {phase.desc}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* Progress Detail */}
            {buildProgress && (
              <div className="border border-[rgba(250,212,192,0.15)] bg-[#FAD4C0]/5 p-8 rounded-3xl space-y-6 shadow-inner">
                <div className="flex justify-between items-baseline">
                  <span className="text-[9px] font-mono font-black text-[#FAD4C0] uppercase tracking-[0.2em] italic">Executing_Task</span>
                  <span className="text-2xl font-mono font-black text-[#FAD4C0]">{buildProgress.progress}%</span>
                </div>
                <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-[#FAD4C0] transition-all duration-700 shadow-[0_0_15px_rgba(250,212,192,0.6)]"
                    style={{ width: `${buildProgress.progress}%` }}
                  />
                </div>
                <div className="flex gap-3">
                  <span className="text-[#FAD4C0] opacity-50 font-mono text-[10px]">{`>>`}</span>
                  <p className="text-[10px] font-mono text-[#FAD4C0]/80 italic leading-relaxed">
                    {buildProgress.message}
                  </p>
                </div>
              </div>
            )}

            {/* Project Info Map */}
            <div className="border border-white/5 rounded-3xl bg-[#0F1117] overflow-hidden pt-6">
              <div className="px-8 flex items-center gap-3 mb-6">
                <div className="w-1.5 h-1.5 bg-[#FAD4C0]/30 rotate-45" />
                <span className="text-[9px] font-mono font-bold text-white/40 uppercase tracking-widest">Metadata_Trace</span>
              </div>
              {projectData && (
                <div className="px-8 pb-8 space-y-4">
                  <div className="flex flex-col gap-1">
                    <span className="text-[9px] font-mono text-white/20 uppercase">Core_Identity</span>
                    <span className="text-xs font-bold text-white truncate pr-4">{projectData.name || "UNNAMED_SEQ"}</span>
                  </div>
                  <div className="flex flex-col gap-1">
                    <span className="text-[9px] font-mono text-white/20 uppercase">Global_Pointer</span>
                    <span className="text-[10px] font-mono text-[#FAD4C0]/60 break-all">{projectData.project_id}</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Launch Action */}
          <div className="p-10 border-t border-white/5 bg-[#161822] shrink-0">
            <button
              onClick={goToNextStep}
              disabled={currentPhase < 2}
              className={`w-full py-6 rounded-2xl font-mono font-black text-sm uppercase tracking-[0.3em] flex justify-between items-center transition-all px-10 group/btn ${currentPhase >= 2
                ? "bg-[#FAD4C0] text-[#111827] shadow-[0_10px_30px_rgba(250,212,192,0.2)] hover:scale-[1.02] active:scale-[0.98] hover:bg-white"
                : "bg-[#1E2030] text-[#A8A3B3]/20 border border-white/5 cursor-not-allowed"
                }`}
            >
              <span>Neural_Initialize</span>
              <span className="group-hover/btn:translate-x-2 transition-transform">→</span>
            </button>
            <div className="mt-8 flex justify-center items-center gap-4">
              <div className="h-px flex-1 bg-white/5" />
              <span className="text-[8px] font-mono text-white/10 uppercase tracking-[0.4em]">Ready_To_Simulate</span>
              <div className="h-px flex-1 bg-white/5" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OntologyProcess;
