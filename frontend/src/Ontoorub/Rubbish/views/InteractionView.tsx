import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft, Maximize2, Minimize2, Settings, Activity,
  ChevronRight, Zap, Database, Globe, MessageSquare, Send,
  Users, Bot, User, Clock, TrendingUp, BarChart3, Mic, MicOff, FileText
} from 'lucide-react';
import { cn } from '@/utils/cn';

// Import components
import GraphPanel from '@/components/ontology/GraphPanel';
import Step5Interaction from '@/components/ontology/Step5Interaction';

// Import APIs
import { graphApi, simulationApi, reportApi } from '@/api/ontology';

interface InteractionViewProps {
  simulationId?: string;
}

export default function InteractionView({ simulationId: propSimulationId }: InteractionViewProps) {
  const navigate = useNavigate();
  const params = useParams();
  const currentSimulationId = propSimulationId || params.simulationId;

  // Layout State
  const [viewMode, setViewMode] = useState<'graph' | 'split' | 'workbench'>('split');
  const [maximizedPanel, setMaximizedPanel] = useState<'graph' | 'workbench' | null>(null);

  // Data State
  const [projectData, setProjectData] = useState<any>(null);
  const [graphData, setGraphData] = useState<any>(null);
  const [graphLoading, setGraphLoading] = useState(false);
  const [systemLogs, setSystemLogs] = useState<any[]>([]);
  const [currentStatus, setCurrentStatus] = useState<'idle' | 'processing' | 'completed' | 'error'>('completed');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [reportData, setReportData] = useState<any>(null);

  // Chat State
  const [messages, setMessages] = useState<any[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<any>(null);
  const [availableAgents, setAvailableAgents] = useState<any[]>([]);
  const [chatMode, setChatMode] = useState<'agent' | 'report'>('agent');

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Initialize data
  useEffect(() => {
    if (currentSimulationId) {
      loadSimulationData();
    }
  }, [currentSimulationId]);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadSimulationData = async () => {
    if (!currentSimulationId) return;
    
    setLoading(true);
    try {
      // Load simulation data
      const simRes = await simulationApi.get(currentSimulationId);
      if (simRes.data.success) {
        const simData = simRes.data.data;
        
        // Load associated project data
        if (simData.project_id) {
          const projectRes = await graphApi.getProject(simData.project_id);
          if (projectRes.data.success) {
            setProjectData(projectRes.data.data);
          }
        }

        // Load graph data if available
        if (simData.graph_id) {
          loadGraphData(simData.graph_id);
        }

        // Load agent profiles
        await loadAgentProfiles();

        // Load report data
        await loadReportData();
      }
    } catch (err) {
      console.error('Failed to load simulation data:', err);
      setError('Failed to load simulation data');
      setCurrentStatus('error');
    } finally {
      setLoading(false);
    }
  };

  const loadGraphData = async (graphId: string) => {
    setGraphLoading(true);
    try {
      const res = await graphApi.getGraphData(graphId);
      if (res.data.success) {
        setGraphData(res.data.data);
      }
    } catch (err) {
      console.error('Failed to load graph data:', err);
    } finally {
      setGraphLoading(false);
    }
  };

  const loadAgentProfiles = async () => {
    if (!currentSimulationId) return;
    
    try {
      // Load Twitter profiles
      const twitterRes = await simulationApi.getProfiles(currentSimulationId, 'twitter');
      const redditRes = await simulationApi.getProfiles(currentSimulationId, 'reddit');
      
      const allAgents = [
        ...(twitterRes.data.success ? twitterRes.data.data.map((p: any) => ({ ...p, platform: 'twitter' })) : []),
        ...(redditRes.data.success ? redditRes.data.data.map((p: any) => ({ ...p, platform: 'reddit' })) : [])
      ];
      
      setAvailableAgents(allAgents);
    } catch (err) {
      console.error('Failed to load agent profiles:', err);
    }
  };

  const loadReportData = async () => {
    if (!currentSimulationId) return;
    
    try {
      const reportRes = await reportApi.getStatus();
      if (reportRes.data.success && reportRes.data.data) {
        setReportData(reportRes.data.data);
      }
    } catch (err) {
      console.error('Failed to load report data:', err);
    }
  };

  const refreshGraph = useCallback(() => {
    if (graphData?.graph_id || projectData?.graph_id) {
      const graphId = graphData?.graph_id || projectData?.graph_id;
      loadGraphData(graphId);
    }
  }, [graphData?.graph_id, projectData?.graph_id]);

  const toggleMaximize = (panel: 'graph' | 'workbench') => {
    if (maximizedPanel === panel) {
      setMaximizedPanel(null);
    } else {
      setMaximizedPanel(panel);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isTyping) return;

    const messageText = inputMessage.trim();
    setInputMessage('');
    
    // Add user message
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: messageText,
      timestamp: new Date().toISOString(),
      agent: selectedAgent
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsTyping(true);

    try {
      let response;
      
      if (chatMode === 'agent' && selectedAgent) {
        // Chat with specific agent
        response = await simulationApi.interviewAgents({
          simulation_id: currentSimulationId!,
          agent_ids: [selectedAgent.agent_id],
          questions: [messageText]
        });
      } else {
        // Chat with report agent
        if (!reportData?.report_id) {
          throw new Error('No report available');
        }
        
        response = await reportApi.chat({
          report_id: reportData.report_id,
          message: messageText,
          history: messages.slice(-10).map(m => ({
            role: m.type === 'user' ? 'user' : 'assistant',
            content: m.content
          }))
        });
      }

      if (response.data.success) {
        const assistantMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          content: response.data.data.response || response.data.data.answer || 'No response received',
          timestamp: new Date().toISOString(),
          agent: chatMode === 'agent' ? selectedAgent : null
        };
        
        setMessages(prev => [...prev, assistantMessage]);
      }
    } catch (err) {
      console.error('Failed to send message:', err);
      
      const errorMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: 'Sorry, I encountered an error processing your message. Please try again.',
        timestamp: new Date().toISOString(),
        agent: null,
        isError: true
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const addLog = useCallback((msg: string, type: string = 'info') => {
    const timestamp = new Date().toISOString();
    setSystemLogs(prev => [...prev, { timestamp, message: msg, type }]);
  }, []);

  const updateStatus = useCallback((status: any, simulating?: boolean) => {
    setCurrentStatus(status);
  }, []);

  // Computed layout styles
  const leftPanelStyle = useMemo(() => {
    if (maximizedPanel === 'graph' || viewMode === 'graph') {
      return { width: '100%', opacity: 1, transform: 'translateX(0)' };
    }
    if (maximizedPanel === 'workbench' || viewMode === 'workbench') {
      return { width: '0%', opacity: 0, transform: 'translateX(-20px)' };
    }
    return { width: '50%', opacity: 1, transform: 'translateX(0)' };
  }, [viewMode, maximizedPanel]);

  const rightPanelStyle = useMemo(() => {
    if (maximizedPanel === 'graph' || viewMode === 'graph') {
      return { width: '0%', opacity: 0, transform: 'translateX(20px)' };
    }
    if (maximizedPanel === 'workbench' || viewMode === 'workbench') {
      return { width: '100%', opacity: 1, transform: 'translateX(0)' };
    }
    return { width: '50%', opacity: 1, transform: 'translateX(0)' };
  }, [viewMode, maximizedPanel]);

  const statusClass = useMemo(() => {
    switch (currentStatus) {
      case 'processing': return 'status-processing';
      case 'completed': return 'status-completed';
      case 'error': return 'status-error';
      default: return 'status-idle';
    }
  }, [currentStatus]);

  const statusText = useMemo(() => {
    switch (currentStatus) {
      case 'processing': return 'Processing...';
      case 'completed': return 'Interactive Mode';
      case 'error': return 'Error';
      default: return 'Ready';
    }
  }, [currentStatus]);

  return (
    <div className="main-view h-screen flex flex-col bg-[#090B10] text-white">
      {/* Header */}
      <header className="app-header h-16 border-b border-white/10 flex items-center justify-between px-6 bg-black/50 backdrop-blur-sm">
        <div className="header-left flex items-center gap-4">
          <button
            onClick={() => navigate('/')}
            className="brand text-xl font-black text-white hover:text-white/80 transition-colors cursor-pointer"
          >
            aarambh
          </button>
        </div>
        
        <div className="header-center">
          <div className="view-switcher flex bg-white/5 rounded-xl p-1">
            {(['graph', 'split', 'workbench'] as const).map((mode) => (
              <button
                key={mode}
                className={cn(
                  "switch-btn px-4 py-2 rounded-lg text-sm font-medium transition-all",
                  viewMode === mode 
                    ? "bg-[var(--accent)] text-[#07080C]" 
                    : "text-white/60 hover:text-white hover:bg-white/10"
                )}
                onClick={() => setViewMode(mode)}
              >
                {mode === 'graph' ? 'Graph' : mode === 'split' ? 'Split' : 'Workbench'}
              </button>
            ))}
          </div>
        </div>

        <div className="header-right flex items-center gap-4">
          <div className="workflow-step flex items-center gap-2 text-sm">
            <span className="step-num text-white/60">Step 5/5</span>
            <span className="step-name text-white font-medium">Deep Interaction</span>
          </div>
          <div className="step-divider w-px h-4 bg-white/20"></div>
          <span className={cn("status-indicator flex items-center gap-2 text-sm", statusClass)}>
            <span className="dot w-2 h-2 rounded-full bg-current"></span>
            {statusText}
          </span>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="content-area flex-1 flex overflow-hidden">
        {/* Left Panel: Graph */}
        <motion.div 
          className="panel-wrapper left border-r border-white/10"
          style={leftPanelStyle}
          transition={{ duration: 0.3, ease: 'easeInOut' }}
        >
          <GraphPanel 
            graphData={graphData}
            loading={graphLoading}
            currentPhase={5}
            onRefresh={refreshGraph}
            onToggleMaximize={() => toggleMaximize('graph')}
          />
        </motion.div>

        {/* Right Panel: Step5 Interaction */}
        <motion.div 
          className="panel-wrapper right overflow-hidden"
          style={rightPanelStyle}
          transition={{ duration: 0.3, ease: 'easeInOut' }}
        >
          <Step5Interaction
            reportId={reportData?.report_id || ''}
            simulationId={currentSimulationId!}
          />
        </motion.div>
      </main>

      {/* Floating Chat Interface (when in split mode) */}
      <AnimatePresence>
        {viewMode === 'split' && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="absolute bottom-6 right-6 bg-black/80 backdrop-blur-md border border-white/10 rounded-2xl w-96 h-[500px] flex flex-col"
          >
            {/* Chat Header */}
            <div className="p-4 border-b border-white/10">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-white flex items-center gap-2">
                  {chatMode === 'agent' ? <Bot className="w-4 h-4" /> : <FileText className="w-4 h-4" />}
                  {chatMode === 'agent' ? 'Agent Chat' : 'Report Chat'}
                </h3>
                <div className="flex gap-2">
                  <button
                    onClick={() => setChatMode(chatMode === 'agent' ? 'report' : 'agent')}
                    className="p-1.5 bg-white/10 hover:bg-white/20 rounded-lg transition-colors text-xs"
                  >
                    Switch
                  </button>
                </div>
              </div>
              
              {chatMode === 'agent' && (
                <select
                  value={selectedAgent?.agent_id || ''}
                  onChange={(e) => {
                    const agent = availableAgents.find(a => a.agent_id === e.target.value);
                    setSelectedAgent(agent || null);
                  }}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white"
                >
                  <option value="">Select an agent...</option>
                  {availableAgents.map((agent) => (
                    <option key={agent.agent_id} value={agent.agent_id}>
                      {agent.username} ({agent.platform})
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={cn(
                    "flex gap-3",
                    message.type === 'user' ? 'justify-end' : 'justify-start'
                  )}
                >
                  {message.type === 'assistant' && (
                    <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0">
                      {chatMode === 'agent' ? <Bot className="w-4 h-4 text-blue-400" /> : <FileText className="w-4 h-4 text-blue-400" />}
                    </div>
                  )}
                  
                  <div
                    className={cn(
                      "max-w-[70%] rounded-xl px-3 py-2 text-sm",
                      message.type === 'user'
                        ? 'bg-[var(--accent)] text-[#07080C]'
                        : message.isError
                        ? 'bg-red-500/20 text-red-300 border border-red-500/50'
                        : 'bg-white/10 text-white'
                    )}
                  >
                    <p>{message.content}</p>
                    {message.agent && (
                      <p className="text-xs opacity-60 mt-1">
                        {message.agent.username} ({message.agent.platform})
                      </p>
                    )}
                  </div>
                  
                  {message.type === 'user' && (
                    <div className="w-8 h-8 rounded-full bg-[var(--accent)]/20 flex items-center justify-center flex-shrink-0">
                      <User className="w-4 h-4 text-[var(--accent)]" />
                    </div>
                  )}
                </div>
              ))}
              
              {isTyping && (
                <div className="flex gap-3 justify-start">
                  <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center">
                    <Bot className="w-4 h-4 text-blue-400 animate-pulse" />
                  </div>
                  <div className="bg-white/10 rounded-xl px-3 py-2 text-sm">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-white/60 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-white/60 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-white/60 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t border-white/10">
              <div className="flex gap-2">
                <input
                  ref={inputRef}
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder={
                    chatMode === 'agent'
                      ? selectedAgent
                        ? `Ask ${selectedAgent.username} anything...`
                        : 'Select an agent to chat with...'
                      : 'Ask about the simulation report...'
                  }
                  disabled={isTyping || (chatMode === 'agent' && !selectedAgent)}
                  className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-white/40 focus:outline-none focus:border-white/20 disabled:opacity-50"
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!inputMessage.trim() || isTyping || (chatMode === 'agent' && !selectedAgent)}
                  className="p-2 bg-[var(--accent)] text-[#07080C] rounded-lg hover:opacity-80 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error Overlay */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="absolute bottom-6 left-6 bg-red-500/20 border border-red-500/50 text-red-300 px-4 py-3 rounded-xl max-w-md"
          >
            <div className="flex items-start gap-3">
              <div className="flex-1">
                <p className="text-sm font-medium">Error</p>
                <p className="text-xs opacity-80 mt-1">{error}</p>
              </div>
              <button
                onClick={() => setError('')}
                className="text-red-400 hover:text-red-300"
              >
                ×
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
