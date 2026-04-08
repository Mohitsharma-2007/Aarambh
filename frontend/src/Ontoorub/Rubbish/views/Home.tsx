import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight, Upload, FileText, Database, Zap, Globe,
  MessageSquare, Users, BarChart3, TrendingUp, Clock,
  ChevronDown, Star, Github, ExternalLink, Play
} from 'lucide-react';
import { cn } from '@/utils/cn';

// Import components
import HistoryDatabase from '@/components/ontology/HistoryDatabase';

// Import APIs
import { graphApi } from '@/api/ontology';

export default function Home() {
  const navigate = useNavigate();

  // Form data
  const [simulationRequirement, setSimulationRequirement] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  
  // Status
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isDragOver, setIsDragOver] = useState(false);

  // File input reference
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Computed property: can submit
  const canSubmit = useMemo(() => {
    return simulationRequirement.trim() !== '' && files.length > 0;
  }, [simulationRequirement, files]);

  // Trigger file selection
  const triggerFileInput = () => {
    if (!loading) {
      fileInputRef.current?.click();
    }
  };

  // Handle file selection
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(event.target.files || []);
    addFiles(selectedFiles);
  };

  // Handle drag & drop
  const handleDragOver = (e: React.DragEvent) => {
    if (!loading) {
      setIsDragOver(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    setIsDragOver(false);
    if (loading) return;
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    addFiles(droppedFiles);
  };

  // Add files
  const addFiles = (newFiles: File[]) => {
    const validFiles = newFiles.filter(file => {
      const ext = file.name.split('.').pop()?.toLowerCase();
      return ['pdf', 'md', 'txt'].includes(ext || '');
    });
    setFiles(prev => [...prev, ...validFiles]);
  };

  // Remove file
  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  // Scroll to bottom
  const scrollToBottom = () => {
    window.scrollTo({
      top: document.body.scrollHeight,
      behavior: 'smooth'
    });
  };

  // Start simulation
  const startSimulation = async () => {
    if (!canSubmit || loading) return;
    
    setLoading(true);
    setError('');
    
    try {
      // Create FormData for file upload
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
      });
      formData.append('simulation_requirement', simulationRequirement);

      // Generate ontology first
      const ontologyRes = await graphApi.generateOntology(formData);
      if (ontologyRes.data.success) {
        const taskId = ontologyRes.data.data.task_id;
        
        // Create project
        const projectRes = await graphApi.buildGraph({
          project_id: taskId,
          chunk_size: 1000,
          chunk_overlap: 200
        });
        
        if (projectRes.data.success) {
          // Navigate to main view with the new project
          navigate(`/ontology/main/${taskId}`);
        }
      }
    } catch (err) {
      console.error('Failed to start simulation:', err);
      setError('Failed to start simulation. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const workflowSteps = [
    {
      num: '01',
      title: 'Knowledge Graph Construction',
      desc: 'Reality Seed Extraction & Individual/Collective Memory Injection & GraphRAG Construction'
    },
    {
      num: '02',
      title: 'Environment Setup',
      desc: 'Entity Relationship Extraction & Persona Generation & Environment Config with Realistic Parameters'
    },
    {
      num: '03',
      title: 'Start Simulation',
      desc: 'Dual-Platform Parallel Simulation & Auto-Analysis of Prediction Needs & Dynamic Timeline Memory Updates'
    },
    {
      num: '04',
      title: 'Report Generation',
      desc: 'ReportAgent with Rich Toolset for Deep Interaction with Post-Simulation Environment'
    },
    {
      num: '05',
      title: 'Deep Interaction',
      desc: 'Chat with Anyone in the Simulated World & Converse with ReportAgent'
    }
  ];

  return (
    <div className="home-container min-h-screen bg-[#090B10] text-white">
      {/* Top Navigation Bar */}
      <nav className="navbar h-16 bg-black border-b border-white/10 flex items-center justify-between px-8">
        <div className="nav-brand text-xl font-black tracking-wider">aarambh</div>
        <div className="nav-links">
          <a 
            href="https://github.com/666ghj/aarambh" 
            target="_blank" 
            rel="noopener noreferrer"
            className="github-link flex items-center gap-2 text-white/80 hover:text-white transition-colors text-sm font-medium"
          >
            Visit our GitHub <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </nav>

      <div className="main-content max-w-7xl mx-auto px-8 py-16">
        {/* Upper Section: Hero Area */}
        <section className="hero-section flex justify-between items-center mb-20">
          <div className="hero-left flex-1 pr-16">
            <div className="tag-row flex items-center gap-4 mb-6">
              <span className="orange-tag bg-[var(--accent)] text-[#07080C] px-3 py-1 text-xs font-black tracking-wider rounded">
                Simple & Universal Collective Intelligence Engine
              </span>
              <span className="version-text text-white/60 text-sm font-medium">/ v0.1-Preview</span>
            </div>
            
            <h1 className="main-title text-6xl font-black leading-tight mb-8 tracking-tight">
              Upload Any Report<br />
              <span className="gradient-text bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
                Instantly Predict the Future
              </span>
            </h1>
            
            <div className="hero-desc text-lg leading-relaxed text-white/70 max-w-2xl mb-12">
              <p className="mb-6">
                Even with just a piece of text, <span className="highlight-bold font-black text-white">aarambh</span> can automatically generate a parallel world composed of up to <span className="highlight-orange text-[var(--accent)] font-black">millions of Agents</span> based on the reality seeds within it. Through a god's-eye view injection of variables, finding <span className="highlight-code bg-white/10 px-2 py-1 rounded font-mono text-sm text-white">"local optimal solutions"</span> in complex group interactions within dynamic environments
              </p>
              <p className="slogan-text text-xl font-black text-white leading-relaxed border-l-4 border-[var(--accent)] pl-6">
                Let the future rehearse among Agents, let decisions prevail after a hundred battles<span className="blinking-cursor text-[var(--accent)] animate-pulse">_</span>
              </p>
            </div>
             
            <div className="decoration-square w-4 h-4 bg-[var(--accent)]"></div>
          </div>
          
          <div className="hero-right flex-0.8 flex flex-col justify-between items-end">
            {/* Logo Area */}
            <div className="logo-container w-full flex justify-end pr-10">
              <img src="/logo.png" alt="Aarambh Logo" className="hero-logo max-w-md w-full" />
            </div>
            
            <button 
              onClick={scrollToBottom}
              className="scroll-down-btn w-12 h-12 border border-white/20 bg-transparent flex items-center justify-center cursor-pointer text-[var(--accent)] text-2xl transition-all hover:border-[var(--accent)] rounded-xl"
            >
              <ChevronDown />
            </button>
          </div>
        </section>

        {/* Lower Section: Two-Column Layout */}
        <section className="dashboard-section flex gap-16 border-t border-white/10 pt-16">
          {/* Left Panel: Status & Steps */}
          <div className="left-panel flex-0.8">
            <div className="panel-header flex items-center gap-2 mb-6">
              <span className="status-dot text-[var(--accent)]">■</span>
              <span className="text-white/60 font-mono text-sm">System Status</span>
            </div>
            
            <h2 className="section-title text-4xl font-black mb-4">Ready to Go</h2>
            <p className="section-desc text-white/70 mb-8 leading-relaxed">
              Prediction engine standing by, upload multiple unstructured data files to initialize simulation sequence
            </p>
            
            {/* Data Metric Cards */}
            <div className="metrics-row flex gap-5 mb-8">
              <div className="metric-card border border-white/10 p-6 min-w-[150px] bg-white/5">
                <div className="metric-value font-mono text-2xl font-black mb-2">Low Cost</div>
                <div className="metric-label text-xs text-white/60">Avg $5/simulation</div>
              </div>
              <div className="metric-card border border-white/10 p-6 min-w-[150px] bg-white/5">
                <div className="metric-value font-mono text-2xl font-black mb-2">High Availability</div>
                <div className="metric-label text-xs text-white/60">Up to Million-Agent Simulation</div>
              </div>
            </div>

            {/* Project Simulation Steps */}
            <div className="steps-container border border-white/10 p-8 bg-white/5">
              <div className="steps-header flex items-center gap-2 mb-8">
                <span className="diamond-icon text-xl">◆</span>
                <span className="text-white/60 font-mono text-sm">Workflow Sequence</span>
              </div>
              <div className="workflow-list flex flex-col gap-6">
                {workflowSteps.map((step, index) => (
                  <div key={index} className="workflow-item flex items-start gap-5">
                    <span className="step-num font-mono font-black text-white/30 text-lg">{step.num}</span>
                    <div className="step-info flex-1">
                      <div className="step-title font-black text-lg mb-2">{step.title}</div>
                      <div className="step-desc text-sm text-white/60 leading-relaxed">{step.desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right Panel: Interaction Console */}
          <div className="right-panel flex-1.2">
            <div className="console-box border border-white/20 p-2 bg-black/50">
              {/* Upload Area */}
              <div className="console-section p-6">
                <div className="console-header flex justify-between items-center mb-4">
                  <span className="console-label font-mono text-xs text-white/60">01 / Reality Seed</span>
                  <span className="console-meta font-mono text-xs text-white/40">Formats: PDF, MD, TXT</span>
                </div>
                
                <div 
                  className={cn(
                    "upload-zone border-2 border-dashed h-48 overflow-y-auto flex items-center justify-center cursor-pointer transition-all bg-white/5",
                    isDragOver ? "border-[var(--accent)] bg-[var(--accent)]/10" : "border-white/20 hover:border-white/40 hover:bg-white/10",
                    files.length > 0 && "items-start"
                  )}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  onClick={triggerFileInput}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept=".pdf,.md,.txt"
                    onChange={handleFileSelect}
                    style={{ display: 'none' }}
                    disabled={loading}
                  />
                  
                  {files.length === 0 ? (
                    <div className="upload-placeholder text-center">
                      <div className="upload-icon w-12 h-12 border border-white/20 flex items-center justify-center mx-auto mb-4 text-white/40">
                        <Upload className="w-6 h-6" />
                      </div>
                      <div className="upload-title font-medium text-white mb-2">Drag & Drop Files</div>
                      <div className="upload-hint font-mono text-xs text-white/40">Or click to browse</div>
                    </div>
                  ) : (
                    <div className="file-list w-full p-4 flex flex-col gap-3">
                      {files.map((file, index) => (
                        <div key={index} className="file-item flex items-center bg-black/50 p-3 rounded-lg border border-white/10 font-mono text-sm">
                          <span className="file-icon mr-3">📄</span>
                          <span className="file-name flex-1 text-white/80">{file.name}</span>
                          <button 
                            onClick={(e) => {
                              e.stopPropagation();
                              removeFile(index);
                            }}
                            className="remove-btn bg-none border-none cursor-pointer text-xl text-white/40 hover:text-white transition-colors"
                          >
                            ×
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Divider */}
              <div className="console-divider flex items-center my-4">
                <div className="flex-1 h-px bg-white/10"></div>
                <span className="px-4 font-mono text-xs text-white/30 uppercase tracking-wider">Input Parameters</span>
                <div className="flex-1 h-px bg-white/10"></div>
              </div>

              {/* Input Area */}
              <div className="console-section p-6">
                <div className="console-header mb-4">
                  <span className="console-label font-mono text-xs text-white/60">&gt;_ 02 / Simulation Prompt</span>
                </div>
                <div className="input-wrapper relative border border-white/20 bg-black/50">
                  <textarea
                    value={simulationRequirement}
                    onChange={(e) => setSimulationRequirement(e.target.value)}
                    className="code-input w-full border-none bg-transparent p-5 font-mono text-sm leading-relaxed resize-none outline-none min-h-[150px] text-white placeholder-white/30"
                    placeholder="// Enter simulation or prediction needs in natural language (e.g., What sentiment trend would emerge if Wuhan University announced revocation of disciplinary action for a student?)"
                    rows={6}
                    disabled={loading}
                  />
                  <div className="model-badge absolute bottom-3 right-3 font-mono text-xs text-white/30">
                    Engine: aarambh-V1.0
                  </div>
                </div>
              </div>

              {/* Launch Button */}
              <div className="console-section btn-section p-6 pt-0">
                <button 
                  className={cn(
                    "start-engine-btn w-full py-6 font-black text-lg flex justify-between items-center cursor-pointer transition-all tracking-wider relative overflow-hidden rounded-xl",
                    canSubmit && !loading 
                      ? "bg-[var(--accent)] text-[#07080C] hover:opacity-90 transform hover:-translate-y-1" 
                      : "bg-white/10 text-white/50 cursor-not-allowed"
                  )}
                  onClick={startSimulation}
                  disabled={!canSubmit || loading}
                >
                  <span>{loading ? 'Initializing...' : 'Launch Engine'}</span>
                  <span className="btn-arrow">
                    {loading ? (
                      <div className="animate-spin">
                        <Play className="w-5 h-5" />
                      </div>
                    ) : (
                      <ArrowRight className="w-5 h-5" />
                    )}
                  </span>
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* History Project Database */}
        <HistoryDatabase />
      </div>

      {/* Error Overlay */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="fixed bottom-8 right-8 bg-red-500/20 backdrop-blur-md border border-red-500/50 text-red-300 px-6 py-4 rounded-2xl max-w-md"
          >
            <div className="flex items-start gap-4">
              <div className="flex-1">
                <p className="text-sm font-medium mb-1">Error</p>
                <p className="text-xs opacity-80">{error}</p>
              </div>
              <button
                onClick={() => setError('')}
                className="text-red-400 hover:text-red-300 text-xl"
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
