import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Shield, Upload, Zap, Activity, Info,
  ChevronDown, ExternalLink, Database, Cpu, Search, Trash2
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { graphApi } from '@/api/ontology';

const StatusBadge = ({ status }: { status: string }) => {
  const isCompleted = status === 'completed';
  const isRunning = status === 'running';
  return (
    <div className={cn(
      "px-2 py-0.5 rounded-full text-[8px] font-black uppercase tracking-widest border",
      isCompleted ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400" :
        isRunning ? "bg-amber-500/10 border-amber-500/20 text-amber-400" :
          "bg-white/5 border-white/10 text-white/40"
    )}>
      {status || 'ACTIVE'}
    </div>
  );
};

export default function OntologyHome() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [simulationRequirement, setSimulationRequirement] = useState('');
  const [loading, setLoading] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const [projects, setProjects] = useState<any[]>([]);
  const [loadingProjects, setLoadingProjects] = useState(true);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const res = await graphApi.listProjects();
      if (res.data.success) setProjects(res.data.data);
    } catch (err) {
      console.error('Failed to load projects:', err);
    } finally {
      setLoadingProjects(false);
    }
  };

  const handleFileAction = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(e.target.files || []);
    const valid = selected.filter(f => ['pdf', 'md', 'txt'].includes(f.name.split('.').pop()?.toLowerCase() || ''));
    setFiles(prev => [...prev, ...valid]);
  };

  const startSimulation = async () => {
    if (!simulationRequirement.trim() || files.length === 0 || loading) return;
    setLoading(true);
    try {
      const formData = new FormData();
      files.forEach(f => formData.append('files', f));
      formData.append('simulation_requirement', simulationRequirement);
      formData.append('project_name', `ONTOLOGY_SEQ_${Date.now().toString().slice(-4)}`);

      const res = await graphApi.generateOntology(formData);
      if (res.data.success) {
        navigate(`/ontology/process/${res.data.data.project_id}`);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#07080C] text-white selection:bg-[var(--accent)]/30 overflow-x-hidden">
      {/* Background Orbs */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-[var(--accent)]/5 blur-[120px] rounded-full" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-[var(--secondary)]/5 blur-[120px] rounded-full" />
      </div>

      <div className="relative z-10 max-w-[1600px] mx-auto px-6 py-12 space-y-16">
        {/* Navigation */}
        <nav className="flex items-center justify-between glass-card !rounded-2xl !p-5">
          <div className="flex items-center gap-4 cursor-pointer" onClick={() => navigate('/ontology')}>
            <div className="p-3 bg-[var(--accent)]/10 rounded-xl text-[var(--accent)]">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xl font-black tracking-tighter">AARAMBH <span className="text-[var(--accent)]">ONTOLOGY</span></span>
              <p className="text-[8px] uppercase tracking-[0.4em] text-white/20 font-black">Collective Intelligence Engine</p>
            </div>
          </div>
          <a href="https://github.com/666ghj/aarambh" target="_blank" className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-white/40 hover:text-[var(--accent)] transition-colors">
            GITHUB REPOSITORY <ExternalLink className="w-3 h-3" />
          </a>
        </nav>

        {/* Hero Section */}
        <section className="grid lg:grid-cols-2 gap-16 items-center pt-8">
          <div className="space-y-10">
            <div className="inline-flex items-center gap-3 px-3 py-1.5 rounded-full bg-white/5 border border-white/10">
              <span className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-pulse" />
              <span className="text-[10px] font-black uppercase tracking-widest text-white/60">V0.1 PREVIEW • EXPERIMENTAL ENGINE</span>
            </div>

            <h1 className="text-7xl font-black tracking-tighter leading-[0.95]">
              UPLOAD ANY REPORT.<br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[var(--accent)] to-[var(--secondary)]">
                PREDICT THE FUTURE.
              </span>
            </h1>

            <p className="text-lg text-white/40 leading-relaxed max-w-xl">
              Construct high-fidelity parallel worlds from unstructured text. Orchestrate million-agent cohorts to simulate complex interactions and identify optimal strategic paths in real-time.
            </p>

            <div className="border-l-4 border-[var(--accent)] pl-8 py-2">
              <p className="text-xl font-black italic tracking-tight text-white/90 italic uppercase">
                Let the future rehearse. Let decisions prevail.
              </p>
            </div>
          </div>

          <div className="relative group">
            <div className="absolute inset-0 bg-[var(--accent)]/10 blur-[100px] group-hover:bg-[var(--accent)]/20 transition-all duration-700" />
            <div className="relative glass-card !p-1 !rounded-[2.5rem] border-white/5">
              <div className="aspect-video bg-[#0D0F14] rounded-[2.2rem] flex items-center justify-center border border-white/5 overflow-hidden">
                <div className="absolute inset-0 opacity-20" style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg viewBox=\'0 0 256 256\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cfilter id=\'n\'%3E%3CfeTurbulence type=\'fractalNoise\' baseFrequency=\'0.85\' numOctaves=\'4\' stitchTiles=\'stitch\'/%3E%3C/filter%3E%3Crect width=\'100%25\' height=\'100%25\' filter=\'url(%23n)\'/%3E%3C/svg%3E")' }} />
                <motion.div
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  className="relative z-10 flex flex-col items-center gap-6"
                >
                  <div className="w-24 h-24 rounded-full bg-gradient-to-tr from-[var(--accent)]/40 to-transparent flex items-center justify-center p-6 border border-white/10">
                    <Activity className="w-full h-full text-[var(--accent)]" />
                  </div>
                  <span className="text-[10px] font-black tracking-[0.6em] text-white/20 uppercase">Core Simulation Engine Locked</span>
                </motion.div>
              </div>
            </div>
          </div>
        </section>

        {/* Dashboard Control Unit */}
        <section className="grid lg:grid-cols-12 gap-8 border-t border-white/5 pt-16">
          {/* Status & Capabilities */}
          <div className="lg:col-span-4 space-y-8">
            <div className="space-y-4">
              <div className="flex items-center gap-3 text-[10px] font-black text-white/30 uppercase tracking-[0.2em]">
                <span className="text-[var(--accent)] font-mono text-lg">■</span> Operational Matrix
              </div>
              <h2 className="text-3xl font-black tracking-tight">READY TO INITIALIZE</h2>
              <p className="text-sm text-white/40 leading-relaxed">
                Connect your unstructured data arrays to begin reality seed extraction and simulation sequence generation.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="glass-card !p-6 !bg-white/[0.02]">
                <span className="text-[32px] font-black text-[var(--accent)] font-mono tracking-tighter">~1M</span>
                <p className="text-[8px] font-black text-white/20 uppercase tracking-widest mt-2">Maximum Agent Capacity</p>
              </div>
              <div className="glass-card !p-6 !bg-white/[0.02]">
                <span className="text-[32px] font-black text-white/80 font-mono tracking-tighter">$5.00</span>
                <p className="text-[8px] font-black text-white/20 uppercase tracking-widest mt-2">Avg. Sequence Energy</p>
              </div>
            </div>

            <div className="glass-card !p-8 space-y-8">
              <span className="text-[9px] font-black text-white/20 uppercase tracking-[0.3em] flex items-center gap-2">
                <div className="w-2 h-2 rotate-45 border border-[var(--accent)]" /> Workflow Sequence Pipeline
              </span>
              <div className="space-y-6">
                {[
                  { id: '01', t: 'Graph Reconstruction', d: 'Seed extraction & semantic memory injection' },
                  { id: '02', t: 'Environment Setup', d: 'Entity mapping & persona cohort building' },
                  { id: '03', t: 'Execution Phase', d: 'Dynamic timeline simulation & branching logic' },
                  { id: '04', t: 'Intelligence Report', d: 'Post-simulation analytical synthesis' },
                  { id: '05', t: 'Deep Interaction', d: 'Direct neural link to simulated entities' },
                ].map(s => (
                  <div key={s.id} className="flex gap-5 group">
                    <span className="text-xl font-black text-white/10 group-hover:text-[var(--accent)]/40 transition-colors font-mono">{s.id}</span>
                    <div>
                      <h4 className="text-sm font-black text-white/80 tracking-tight">{s.t}</h4>
                      <p className="text-[10px] text-white/30 uppercase tracking-wide mt-1 leading-relaxed">{s.d}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Console / Command Terminal */}
          <div className="lg:col-span-8">
            <div className="glass-card !p-1 !rounded-[2rem] border-white/10 h-full">
              <div className="bg-[#090B10] rounded-[1.8rem] h-full flex flex-col">
                {/* File Upload Section */}
                <div className="p-10 space-y-6">
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-black text-white/30 uppercase tracking-[0.3em]">01 / Reality Seed Input</span>
                    <span className="text-[8px] font-bold text-white/10 uppercase tracking-widest">Formats supported: PDF, MD, TXT</span>
                  </div>

                  <div
                    onClick={() => fileInputRef.current?.click()}
                    onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
                    onDragLeave={() => setIsDragOver(false)}
                    onDrop={(e) => { e.preventDefault(); setIsDragOver(false); handleFileAction({ target: { files: e.dataTransfer.files } } as any); }}
                    className={cn(
                      "group border-2 border-dashed rounded-3xl min-h-[250px] flex flex-col items-center justify-center transition-all cursor-pointer",
                      isDragOver ? "border-[var(--accent)] bg-[var(--accent)]/5" : "border-white/5 hover:bg-white/[0.02] hover:border-white/10"
                    )}
                  >
                    <input ref={fileInputRef} type="file" multiple accept=".pdf,.md,.txt" onChange={handleFileAction} className="hidden" />

                    {files.length === 0 ? (
                      <div className="text-center space-y-4">
                        <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/5 flex items-center justify-center mx-auto text-white/20 group-hover:scale-110 group-hover:text-[var(--accent)] transition-all">
                          <Upload className="w-6 h-6" />
                        </div>
                        <div className="space-y-1">
                          <p className="text-sm font-black tracking-tight text-white/60">INGEST INFORMATION</p>
                          <p className="text-[9px] font-bold text-white/20 uppercase tracking-widest">Drag & Drop or Click to Browse</p>
                        </div>
                      </div>
                    ) : (
                      <div className="w-full p-8 grid sm:grid-cols-2 gap-4">
                        {files.map((f, i) => (
                          <div key={i} className="flex items-center gap-3 bg-white/5 border border-white/5 p-4 rounded-2xl group/file">
                            <div className="p-2 bg-[var(--accent)]/10 rounded-lg text-[var(--accent)]"><Zap className="w-3.5 h-3.5" /></div>
                            <span className="flex-1 text-[11px] font-black text-white/60 truncate font-mono uppercase italic">{f.name}</span>
                            <button onClick={(e) => { e.stopPropagation(); setFiles(prev => prev.filter((_, idx) => idx !== i)); }} className="p-1 hover:text-red-500 transition-colors opacity-0 group-hover/file:opacity-100">
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        ))}
                        <div className="flex items-center justify-center p-4 border border-dashed border-white/5 rounded-2xl text-[9px] font-black text-white/20 uppercase tracking-widest hover:text-white/40 transition-colors">
                          + Append Sources
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                <div className="h-px bg-white/5 flex-none" />

                {/* Prompt Section */}
                <div className="p-10 space-y-6 flex-1 flex flex-col">
                  <span className="text-[10px] font-black text-white/30 uppercase tracking-[0.3em]">{">_"} 02 / Command Protocol</span>
                  <div className="flex-1 bg-black/40 border border-white/5 rounded-2xl p-6 focus-within:border-[var(--accent)]/40 transition-all relative">
                    <textarea
                      value={simulationRequirement}
                      onChange={(e) => setSimulationRequirement(e.target.value)}
                      placeholder="INITIATE PREDICTION SEQUENCE: DESCRIBE FUTURE ANALYSIS OBJECTIVE..."
                      className="w-full h-full bg-transparent border-none outline-none resize-none text-sm font-mono text-[var(--accent)] placeholder:text-white/5 font-bold leading-relaxed uppercase"
                    />
                    <div className="absolute bottom-6 right-6 text-[8px] font-black text-white/5 uppercase tracking-[0.4em]">Engine: V1.0.OA-KRNL</div>
                  </div>
                </div>

                {/* Submit */}
                <div className="p-10 pt-0 flex-none">
                  <button
                    onClick={startSimulation}
                    disabled={!simulationRequirement.trim() || files.length === 0 || loading}
                    className={cn(
                      "w-full h-20 rounded-[1.2rem] flex items-center justify-between px-10 transition-all active:scale-[0.98]",
                      (simulationRequirement.trim() && files.length > 0 && !loading)
                        ? "bg-[var(--accent)] text-[#07080C] shadow-[0_0_50px_rgba(var(--accent-rgb),0.2)] hover:bg-white"
                        : "bg-white/5 text-white/10 cursor-not-allowed border border-white/5"
                    )}
                  >
                    <span className="text-xl font-black uppercase tracking-[0.3em]">
                      {loading ? 'INITIALIZING sequence...' : 'Execute Simulation'}
                    </span>
                    <Cpu className={cn("w-6 h-6", loading && "animate-spin")} />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Node Archive Section */}
        <section className="border-t border-white/5 pt-20 pb-20">
          <div className="flex items-end justify-between mb-12">
            <div>
              <div className="flex items-center gap-2 text-[10px] font-black text-white/30 uppercase tracking-[0.3em] mb-4">
                <Database className="w-3.5 h-3.5 text-[var(--accent)]" /> Global Node Archive
              </div>
              <h2 className="text-5xl font-black tracking-tighter">HISTORICAL SNAPSHOTS</h2>
            </div>
            <div className="px-5 py-2.5 rounded-xl border border-white/5 bg-white/[0.02] text-[10px] font-black uppercase tracking-widest text-white/40">
              ACTIVE NODES: {projects.length}
            </div>
          </div>

          {loadingProjects ? (
            <div className="grid md:grid-cols-3 gap-8">
              {[1, 2, 3].map(i => <div key={i} className="h-64 rounded-3xl bg-white/[0.02] border border-white/5 animate-pulse" />)}
            </div>
          ) : projects.length === 0 ? (
            <div className="h-80 rounded-[3rem] border-2 border-dashed border-white/5 flex flex-col items-center justify-center text-white/15 space-y-6">
              <Zap className="w-12 h-12 opacity-50" />
              <p className="text-sm font-black uppercase tracking-[0.5em]">Archive empty. Initiate first sequence.</p>
            </div>
          ) : (
            <div className="grid md:grid-cols-3 gap-8">
              {projects.map((p) => (
                <div
                  key={p.project_id}
                  onClick={() => navigate(`/ontology/process/${p.project_id}`)}
                  className="group relative glass-card !p-8 !rounded-[2rem] border-white/5 hover:border-[var(--accent)]/40 hover:bg-[var(--accent)]/[0.02] transition-all cursor-pointer"
                >
                  <div className="absolute top-0 left-0 w-1 h-full bg-[var(--accent)] opacity-0 group-hover:opacity-40 transition-opacity" />
                  <div className="flex items-center justify-between mb-8">
                    <span className="font-mono text-[9px] text-white/20 uppercase tracking-tighter bg-white/5 px-2 py-0.5 rounded">UID: {p.project_id.slice(0, 8)}</span>
                    <StatusBadge status={p.status} />
                  </div>
                  <h3 className="text-xl font-black truncate pr-4 text-white group-hover:text-[var(--accent)] transition-colors mb-2 uppercase">{p.project_name}</h3>
                  <div className="flex items-center gap-3 mt-10 text-[9px] font-black text-white/10 uppercase tracking-widest">
                    <span>CREATED AT</span>
                    <div className="h-px bg-white/10 flex-1" />
                    <span>{new Date(p.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
