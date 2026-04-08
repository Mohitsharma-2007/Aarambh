import React, { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { reportApi, simulationApi } from '../api/ontology'

interface LogEntry {
  time: string
  message: string
  type: 'info' | 'success' | 'error' | 'warning'
}

interface AgentProfile {
  agent_id: string
  username: string
  bio?: string
  profession?: string
  name?: string
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

interface ReportOutline {
  title: string
  summary: string
  sections: Array<{ title: string; description?: string }>
}

const STEPS = [
  { num: 1, title: 'Graph Construction', icon: '⬡' },
  { num: 2, title: 'Environment Setup', icon: '⚙' },
  { num: 3, title: 'Simulation', icon: '▶' },
  { num: 4, title: 'Report', icon: '📊' },
  { num: 5, title: 'Interaction', icon: '💬' },
]

export const OntologyInteraction: React.FC = () => {
  const { reportId: routeReportId } = useParams()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const chatMessagesRef = useRef<HTMLDivElement>(null)
  const logEndRef = useRef<HTMLDivElement>(null)

  // Get params from URL
  const projectId = searchParams.get('projectId') || ''
  const graphId = searchParams.get('graphId') || ''
  const simulationIdParam = searchParams.get('simulationId') || ''

  // State
  const [reportId, setReportId] = useState(routeReportId || '')
  const [simulationId, setSimulationId] = useState(simulationIdParam)
  const [currentStep, setCurrentStep] = useState(5)
  const [status, setStatus] = useState<'ready' | 'processing' | 'completed' | 'error'>('ready')

  // Report state
  const [reportOutline, setReportOutline] = useState<ReportOutline | null>(null)
  const [generatedSections, setGeneratedSections] = useState<Record<number, string>>({})
  const [collapsedSections, setCollapsedSections] = useState<Set<number>>(new Set())

  // Agent profiles
  const [profiles, setProfiles] = useState<AgentProfile[]>([])

  // Chat state
  const [activeTab, setActiveTab] = useState<'chat' | 'survey'>('chat')
  const [chatTarget, setChatTarget] = useState<'report_agent' | 'agent'>('report_agent')
  const [selectedAgent, setSelectedAgent] = useState<AgentProfile | null>(null)
  const [selectedAgentIndex, setSelectedAgentIndex] = useState<number | null>(null)
  const [showAgentDropdown, setShowAgentDropdown] = useState(false)
  const [chatInput, setChatInput] = useState('')
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([])
  const [chatHistoryCache, setChatHistoryCache] = useState<Record<string, ChatMessage[]>>({})
  const [isSending, setIsSending] = useState(false)

  // Survey state
  const [selectedAgents, setSelectedAgents] = useState<Set<number>>(new Set())
  const [surveyQuestion, setSurveyQuestion] = useState('')
  const [surveyResults, setSurveyResults] = useState<Array<{
    agent_id: number
    agent_name: string
    profession?: string
    question: string
    answer: string
  }>>([])
  const [isSurveying, setIsSurveying] = useState(false)

  // Logs
  const [logs, setLogs] = useState<LogEntry[]>([])

  // Helpers
  const addLog = useCallback((message: string, type: LogEntry['type'] = 'info') => {
    const time = new Date().toLocaleTimeString('en-US', { hour12: false })
    setLogs(prev => [...prev, { time, message, type }])
  }, [])

  // Load data on mount
  useEffect(() => {
    if (reportId) {
      loadReportData()
    }
    if (simulationId) {
      loadProfiles()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reportId, simulationId])

  const loadReportData = async () => {
    if (!reportId) return

    try {
      addLog(`Loading report: ${reportId}`, 'info')
      const res = await reportApi.get(reportId)
      if (res.data.success && res.data.data) {
        const data = res.data.data
        setReportOutline(data.outline)
        setGeneratedSections(data.sections || {})
        if (data.simulation_id) {
          setSimulationId(data.simulation_id)
        }
        addLog('Report loaded', 'success')
      }

      // Load agent logs
      const logRes = await reportApi.getAgentLog(reportId, 0)
      if (logRes.data.success && logRes.data.data?.logs) {
        processAgentLogs(logRes.data.data.logs)
      }
    } catch (err: any) {
      addLog(`Failed to load report: ${err.message}`, 'error')
    }
  }

  const loadProfiles = async () => {
    if (!simulationId) return

    try {
      const [twitterRes, redditRes] = await Promise.all([
        simulationApi.getProfiles(simulationId, 'twitter'),
        simulationApi.getProfiles(simulationId, 'reddit'),
      ])

      const twitterProfiles = twitterRes.data.data || []
      const redditProfiles = redditRes.data.data || []

      // Combine profiles
      const allProfiles = [...twitterProfiles, ...redditProfiles]
      setProfiles(allProfiles)
      addLog(`Loaded ${allProfiles.length} agent profiles`, 'info')
    } catch (err: any) {
      addLog(`Failed to load profiles: ${err.message}`, 'error')
    }
  }

  const processAgentLogs = (logs: any[]) => {
    for (const log of logs) {
      if (log.action === 'planning_complete' && log.details?.outline) {
        setReportOutline(log.details.outline)
      } else if (log.action === 'section_content' && log.section_index) {
        setGeneratedSections(prev => ({
          ...prev,
          [log.section_index]: log.details?.content || ''
        }))
      }
    }
  }

  // Chat methods
  const saveChatHistory = useCallback(() => {
    if (chatHistory.length === 0) return

    const key = chatTarget === 'report_agent' ? 'report_agent' : `agent_${selectedAgentIndex}`
    setChatHistoryCache(prev => ({
      ...prev,
      [key]: [...chatHistory]
    }))
  }, [chatHistory, chatTarget, selectedAgentIndex])

  const restoreChatHistory = useCallback((key: string) => {
    setChatHistory(chatHistoryCache[key] || [])
  }, [chatHistoryCache])

  const selectReportAgentChat = () => {
    saveChatHistory()
    setActiveTab('chat')
    setChatTarget('report_agent')
    setSelectedAgent(null)
    setSelectedAgentIndex(null)
    setShowAgentDropdown(false)
    restoreChatHistory('report_agent')
  }

  const selectAgent = (agent: AgentProfile, idx: number) => {
    saveChatHistory()
    setSelectedAgent(agent)
    setSelectedAgentIndex(idx)
    setChatTarget('agent')
    setShowAgentDropdown(false)
    restoreChatHistory(`agent_${idx}`)
    addLog(`Selected chat target: ${agent.username}`)
  }

  const sendMessage = async () => {
    if (!chatInput.trim() || isSending) return

    const message = chatInput.trim()
    setChatInput('')

    // Add user message
    const userMsg: ChatMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    }
    setChatHistory(prev => [...prev, userMsg])
    scrollToBottom()
    setIsSending(true)

    try {
      if (chatTarget === 'report_agent') {
        await sendToReportAgent(message)
      } else {
        await sendToAgent(message)
      }
    } catch (err: any) {
      addLog(`Send failed: ${err.message}`, 'error')
      setChatHistory(prev => [...prev, {
        role: 'assistant',
        content: `Sorry, an error occurred: ${err.message}`,
        timestamp: new Date().toISOString()
      }])
    } finally {
      setIsSending(false)
      scrollToBottom()
    }
  }

  const sendToReportAgent = async (message: string) => {
    addLog(`Sending to Report Agent: ${message.substring(0, 50)}...`)

    const historyForApi = chatHistory
      .filter(msg => msg.content !== message)
      .slice(-10)
      .map(msg => ({ role: msg.role, content: msg.content }))

    const res = await reportApi.chat({
      report_id: reportId,
      message: message,
      history: historyForApi
    })

    if (res.data.success && res.data.data) {
      const response = res.data.data.response || res.data.data.answer || 'No response'
      setChatHistory(prev => [...prev, {
        role: 'assistant',
        content: response,
        timestamp: new Date().toISOString()
      }])
      addLog('Report Agent responded', 'success')
    } else {
      throw new Error(res.data.error || 'Request failed')
    }
  }

  const sendToAgent = async (message: string) => {
    if (!selectedAgent || selectedAgentIndex === null) {
      throw new Error('Please select an agent first')
    }

    addLog(`Sending to ${selectedAgent.username}: ${message.substring(0, 50)}...`)

    const res = await simulationApi.interviewAgents({
      simulation_id: simulationId,
      agent_ids: [String(selectedAgentIndex)],
      questions: [message]
    })

    if (res.data.success && res.data.data) {
      const resultsDict = res.data.data.results || res.data.data
      let responseContent = 'No response'

      if (typeof resultsDict === 'object' && !Array.isArray(resultsDict)) {
        const redditKey = `reddit_${selectedAgentIndex}`
        const twitterKey = `twitter_${selectedAgentIndex}`
        const agentResult = resultsDict[redditKey] || resultsDict[twitterKey] || Object.values(resultsDict)[0]
        if (agentResult) {
          responseContent = (agentResult as any).response || (agentResult as any).answer || 'No response'
        }
      }

      setChatHistory(prev => [...prev, {
        role: 'assistant',
        content: responseContent,
        timestamp: new Date().toISOString()
      }])
      addLog(`${selectedAgent.username} responded`, 'success')
    } else {
      throw new Error(res.data.error || 'Request failed')
    }
  }

  const scrollToBottom = () => {
    setTimeout(() => {
      chatMessagesRef.current?.scrollTo({
        top: chatMessagesRef.current.scrollHeight,
        behavior: 'smooth'
      })
    }, 100)
  }

  // Survey methods
  const toggleAgentSelection = (idx: number) => {
    setSelectedAgents(prev => {
      const newSet = new Set(prev)
      if (newSet.has(idx)) {
        newSet.delete(idx)
      } else {
        newSet.add(idx)
      }
      return newSet
    })
  }

  const selectAllAgents = () => {
    const newSet = new Set<number>()
    profiles.forEach((_, idx) => newSet.add(idx))
    setSelectedAgents(newSet)
  }

  const clearAgentSelection = () => {
    setSelectedAgents(new Set())
  }

  const submitSurvey = async () => {
    if (selectedAgents.size === 0 || !surveyQuestion.trim() || isSurveying) return

    setIsSurveying(true)
    addLog(`Sending survey to ${selectedAgents.size} agents...`)

    try {
      const agentIds = Array.from(selectedAgents).map(String)
      const questions = Array.from(selectedAgents).map(() => surveyQuestion.trim())

      const res = await simulationApi.interviewAgents({
        simulation_id: simulationId,
        agent_ids: agentIds,
        questions: questions
      })

      if (res.data.success && res.data.data) {
        const resultsDict = res.data.data.results || res.data.data
        const resultsList: any[] = []

        Array.from(selectedAgents).forEach((idx, i) => {
          const agent = profiles[idx]
          let responseContent = 'No response'

          if (typeof resultsDict === 'object' && !Array.isArray(resultsDict)) {
            const redditKey = `reddit_${idx}`
            const twitterKey = `twitter_${idx}`
            const agentResult = resultsDict[redditKey] || resultsDict[twitterKey]
            if (agentResult) {
              responseContent = (agentResult as any).response || (agentResult as any).answer || 'No response'
            }
          }

          resultsList.push({
            agent_id: idx,
            agent_name: agent?.username || `Agent ${idx}`,
            profession: agent?.profession,
            question: surveyQuestion.trim(),
            answer: responseContent
          })
        })

        setSurveyResults(resultsList)
        addLog(`Received ${resultsList.length} responses`, 'success')
      }
    } catch (err: any) {
      addLog(`Survey failed: ${err.message}`, 'error')
    } finally {
      setIsSurveying(false)
    }
  }

  const toggleSectionCollapse = (idx: number) => {
    setCollapsedSections(prev => {
      const newSet = new Set(prev)
      if (newSet.has(idx)) {
        newSet.delete(idx)
      } else {
        newSet.add(idx)
      }
      return newSet
    })
  }

  const isSectionCompleted = (idx: number) => {
    return generatedSections[idx] !== undefined
  }

  const formatTime = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' })
    } catch {
      return ''
    }
  }

  return (
    <div className="h-screen bg-[#0F1117] text-[#F5F0EB] font-['Inter',sans-serif] flex flex-col overflow-hidden">
      {/* Workflow Stepper */}
      <nav className="h-[60px] bg-[#161822] border-b border-[rgba(250,212,192,0.12)] flex items-center px-8 shrink-0">
        <div className="flex items-center gap-8">
          <div className="font-extrabold text-xl tracking-wider text-[#FAD4C0] cursor-pointer" onClick={() => navigate(-1)}>AARAMBH</div>
          <div className="h-4 w-px bg-white/10" />
          <div className="flex items-center gap-1.5">
            {STEPS.map((step, i) => (
              <React.Fragment key={step.num}>
                <div
                  className={`flex items-center gap-3 px-4 py-1.5 rounded-full text-[10px] font-mono font-black uppercase tracking-widest transition-all border ${step.num === currentStep
                    ? 'bg-[#FAD4C0] text-[#111827] border-[#FAD4C0]'
                    : step.num < currentStep
                      ? 'bg-[#16A34A]/10 text-[#16A34A] border-[#16A34A]/20 cursor-default'
                      : 'bg-white/5 text-white/20 border-white/5 opacity-50'
                    }`}
                >
                  <span className="opacity-50">{step.icon}</span>
                  <span>{step.title}</span>
                </div>
                {i < STEPS.length - 1 && (
                  <div className="w-4 h-px bg-white/5" />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </nav>

      <main className="flex-1 overflow-hidden p-10 flex gap-10">
        {/* Left - Report Panel */}
        <div className="flex-1 flex flex-col bg-[#161822] border border-white/5 rounded-3xl overflow-hidden shadow-2xl">
          <div className="px-10 py-6 border-b border-white/5 flex items-center justify-between bg-[#1A1C2A]/30 shrink-0">
            <div className="flex items-center gap-4">
              <span className="text-[10px] font-mono font-black text-white uppercase tracking-widest italic">PREDICTION_RECORD</span>
              <span className="text-[9px] font-mono text-white/20 uppercase tracking-widest">ID: {reportId?.slice(0, 8)}</span>
            </div>
            <button
              onClick={loadReportData}
              className="px-5 py-2 bg-[#FAD4C0]/5 border border-[#FAD4C0]/20 text-[#FAD4C0] text-[9px] font-mono font-bold uppercase rounded hover:bg-[#FAD4C0] hover:text-[#111827] transition-all"
            >
              Manual_Sync
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-12 space-y-12 scrollbar-thin scrollbar-thumb-white/5 selection:bg-[#FAD4C0] selection:text-[#111827]">
            {reportOutline ? (
              <article className="max-w-3xl mx-auto space-y-12">
                <header className="space-y-4">
                  <span className="px-3 py-1 bg-[#FAD4C0]/10 text-[#FAD4C0] text-[9px] font-mono font-black rounded-lg border border-[#FAD4C0]/20 uppercase tracking-widest">Active_Intelligence_Buffer</span>
                  <h1 className="text-3xl font-black text-white uppercase tracking-tight font-mono p-1 italic border-l-4 border-[#FAD4C0] pl-6">{reportOutline.title}</h1>
                  <p className="text-sm text-[#A8A3B3] leading-relaxed font-medium italic opacity-70">
                    {reportOutline.summary}
                  </p>
                </header>

                <section className="space-y-6">
                  {reportOutline.sections.map((section, idx) => (
                    <div
                      key={idx}
                      className={`border rounded-3xl overflow-hidden transition-all ${isSectionCompleted(idx + 1)
                        ? 'border-white/5 bg-[#0F1117]/50'
                        : 'border-white/5 opacity-40'
                        }`}
                    >
                      <div
                        onClick={() => isSectionCompleted(idx + 1) && toggleSectionCollapse(idx)}
                        className={`flex items-center gap-6 px-8 py-5 ${isSectionCompleted(idx + 1) ? 'cursor-pointer hover:bg-white/5' : ''
                          }`}
                      >
                        <span className={`text-[10px] font-mono font-black ${isSectionCompleted(idx + 1) ? 'text-[#16A34A]' : 'text-white/20'
                          }`}>
                          S_{String(idx + 1).padStart(2, '0')}
                        </span>
                        <h3 className="text-[11px] font-black text-white uppercase tracking-widest flex-1">{section.title}</h3>
                        {isSectionCompleted(idx + 1) && (
                          <span className={`text-white/20 transition-transform ${collapsedSections.has(idx) ? 'rotate-180' : ''}`}>↓</span>
                        )}
                      </div>

                      {!collapsedSections.has(idx) && generatedSections[idx + 1] && (
                        <div className="px-10 py-8 border-t border-white/5 bg-[#1A1C2B]/20">
                          <div className="space-y-4">
                            {generatedSections[idx + 1].split('\n').map((p, i) => (
                              <p key={i} className="text-sm text-[#F5F0EB]/70 leading-relaxed font-medium">
                                {p}
                              </p>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </section>
              </article>
            ) : (
              <div className="h-full flex items-center justify-center">
                <span className="text-xs font-mono font-black text-white/20 uppercase tracking-[0.4em] animate-pulse">Syncing_Neural_Buffers...</span>
              </div>
            )}
          </div>
        </div>

        {/* Right - Interaction Interface */}
        <div className="w-[500px] flex flex-col bg-[#161822] border border-white/5 rounded-3xl overflow-hidden shadow-2xl">
          <div className="px-10 py-8 border-b border-white/5 bg-[#1A1C2A]/30 flex flex-col gap-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 bg-[#FAD4C0]/10 border border-[#FAD4C0]/20 rounded-xl flex items-center justify-center text-[#FAD4C0]">⬡</div>
                <div className="space-y-0.5">
                  <h3 className="text-xs font-black text-white uppercase tracking-widest italic">NEURAL_INTERFACE</h3>
                  <p className="text-[9px] font-mono text-white/30 uppercase tracking-widest">{profiles.length} OPERATIVE_NODES_LIVE</p>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => setActiveTab('chat')}
                  className={`px-4 py-2 text-[9px] font-mono font-black uppercase rounded-lg border transition-all ${activeTab === 'chat' ? 'bg-[#FAD4C0] border-[#FAD4C0] text-[#111827]' : 'border-white/5 text-white/40 hover:border-white/10'
                    }`}
                >Chat</button>
                <button
                  onClick={() => setActiveTab('survey')}
                  className={`px-4 py-2 text-[9px] font-mono font-black uppercase rounded-lg border transition-all ${activeTab === 'survey' ? 'bg-[#FAD4C0] border-[#FAD4C0] text-[#111827]' : 'border-white/5 text-white/40 hover:border-white/10'
                    }`}
                >Survey</button>
              </div>
            </div>

            <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-none">
              <button
                onClick={selectReportAgentChat}
                className={`flex-none px-4 py-2 rounded-xl text-[9px] font-mono font-black uppercase transition-all flex items-center gap-3 border ${activeTab === 'chat' && chatTarget === 'report_agent'
                  ? 'bg-purple-500/20 text-purple-400 border-purple-500/30'
                  : 'bg-[#0F1117] text-white/40 border-white/5 hover:border-white/20'
                  }`}
              >
                <span className="w-2 h-2 rounded-full bg-purple-500 animate-pulse" />
                REPORT_CORE
              </button>

              <div className="relative flex-none">
                <button
                  onClick={() => setShowAgentDropdown(!showAgentDropdown)}
                  className={`px-4 py-2 rounded-xl text-[9px] font-mono font-black uppercase transition-all flex items-center gap-3 border ${activeTab === 'chat' && chatTarget === 'agent'
                    ? 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                    : 'bg-[#0F1117] text-white/40 border-white/5 hover:border-white/20'
                    }`}
                >
                  <span className="w-2 h-2 rounded-full bg-blue-500" />
                  {selectedAgent ? selectedAgent.username : 'AGENT_NODE'}
                  <span className="text-[7px]">▼</span>
                </button>

                {showAgentDropdown && (
                  <div className="absolute top-full left-0 mt-3 w-72 bg-[#1A1C2A] border border-white/10 rounded-2xl shadow-2xl z-50 max-h-80 overflow-y-auto scrollbar-thin">
                    <div className="px-5 py-4 text-[9px] font-mono text-white/20 border-b border-white/5 uppercase tracking-widest">Select_Node_Input</div>
                    {profiles.map((agent, idx) => (
                      <div
                        key={idx}
                        onClick={() => selectAgent(agent, idx)}
                        className="flex items-center gap-4 px-5 py-3.5 hover:bg-white/5 cursor-pointer group transition-colors"
                      >
                        <div className="w-8 h-8 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-[10px] font-black text-blue-400 group-hover:bg-blue-500 group-hover:text-white transition-all">
                          {(agent.username || 'A')[0]}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-[11px] font-bold text-white uppercase group-hover:text-[#FAD4C0] transition-colors">{agent.username}</div>
                          <div className="text-[9px] font-mono text-white/20 truncate uppercase">{agent.profession || 'UNKNOWN_PROF'}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="flex-1 flex flex-col min-h-0">
            {activeTab === 'chat' && (
              <>
                <div ref={chatMessagesRef} className="flex-1 overflow-y-auto p-10 space-y-8 scrollbar-thin scrollbar-thumb-white/5">
                  {chatHistory.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center gap-8 opacity-20">
                      <div className="w-20 h-20 border-4 border-dotted border-white/20 rounded-full animate-[spin_20s_linear_infinite] flex items-center justify-center">
                        <div className="w-12 h-12 bg-white/10 rounded-full" />
                      </div>
                      <p className="text-[10px] font-mono text-center uppercase tracking-widest max-w-[250px] leading-relaxed">
                        Establish connection with intelligence cores to refine neural output
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-10">
                      {chatHistory.map((msg, idx) => (
                        <div key={idx} className={`flex gap-6 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                          <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-xs font-black shrink-0 border ${msg.role === 'user'
                            ? 'bg-[#FAD4C0]/10 border-[#FAD4C0]/20 text-[#FAD4C0]'
                            : chatTarget === 'report_agent'
                              ? 'bg-purple-500/10 border-purple-500/20 text-purple-400'
                              : 'bg-blue-500/10 border-blue-500/20 text-blue-400'
                            }`}>
                            {msg.role === 'user' ? 'U' : chatTarget === 'report_agent' ? 'R' : (selectedAgent?.username?.[0] || 'A')}
                          </div>

                          <div className={`flex-1 space-y-3 ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
                            <div className={`text-[9px] font-mono text-white/30 uppercase tracking-widest flex items-center gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                              <span>{msg.role === 'user' ? 'Terminal_User' : (chatTarget === 'report_agent' ? 'Report_Agent' : selectedAgent?.username)}</span>
                              <span className="w-1 h-1 bg-white/10 rounded-full" />
                              <span>{formatTime(msg.timestamp)}</span>
                            </div>
                            <div className={`inline-block px-8 py-5 rounded-3xl text-sm leading-relaxed font-medium selection:bg-[#FAD4C0] selection:text-[#111827] ${msg.role === 'user'
                              ? 'bg-[#FAD4C0] text-[#111827] rounded-tr-none'
                              : 'bg-[#0F1117] text-[#F5F0EB]/90 border border-white/5 rounded-tl-none'
                              }`}>
                              {msg.content}
                            </div>
                          </div>
                        </div>
                      ))}
                      {isSending && (
                        <div className="flex gap-6 animate-pulse">
                          <div className="w-10 h-10 bg-white/5 border border-white/5 rounded-xl flex items-center justify-center text-[10px] font-black italic">...</div>
                          <div className="flex-1 space-y-2">
                            <div className="w-24 h-2 bg-white/5 rounded-full" />
                            <div className="w-full h-12 bg-white/5 rounded-3xl" />
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <div className="px-10 py-8 border-t border-white/5 bg-[#1A1C2A]/20">
                  <div className="flex gap-4 p-2 bg-[#0F1117] border border-white/10 rounded-2xl items-center shadow-xl">
                    <input
                      type="text"
                      value={chatInput}
                      onChange={e => setChatInput(e.target.value)}
                      onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                      placeholder={chatTarget === 'agent' && !selectedAgent ? "Select target node..." : "Transmit intelligence query..."}
                      disabled={isSending || (chatTarget === 'agent' && !selectedAgent)}
                      className="flex-1 bg-transparent py-4 px-6 text-sm text-white placeholder:text-white/10 focus:outline-none disabled:opacity-30"
                    />
                    <button
                      onClick={sendMessage}
                      disabled={!chatInput.trim() || isSending || (chatTarget === 'agent' && !selectedAgent)}
                      className="w-12 h-12 bg-[#FAD4C0] hover:bg-white text-[#111827] rounded-xl flex items-center justify-center transition-all disabled:opacity-10 active:scale-95"
                    >
                      <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" /></svg>
                    </button>
                  </div>
                </div>
              </>
            )}

            {activeTab === 'survey' && (
              <div className="p-10 space-y-10 overflow-y-auto flex-1 scrollbar-thin">
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <h4 className="text-[10px] font-mono font-black text-[#FAD4C0] uppercase tracking-widest italic">Node_Cluster_Selection</h4>
                    <div className="flex items-center gap-4 text-[10px] font-mono text-white/30 uppercase">
                      <button onClick={selectAllAgents} className="hover:text-white transition-colors">Select_All</button>
                      <span>/</span>
                      <button onClick={clearAgentSelection} className="hover:text-white transition-colors">Clear</button>
                      <span className="bg-white/5 px-3 py-1 rounded-full text-white ml-2">{selectedAgents.size}_TARGETS</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 max-h-[300px] overflow-y-auto pr-4 scrollbar-thin">
                    {profiles.map((agent, idx) => (
                      <div
                        key={idx}
                        onClick={() => toggleAgentSelection(idx)}
                        className={`group flex items-center gap-4 p-4 rounded-2xl cursor-pointer border transition-all ${selectedAgents.has(idx)
                          ? 'bg-[#16A34A]/10 border-[#16A34A]/40'
                          : 'bg-[#0F1117] border-white/5 hover:border-white/10'
                          }`}
                      >
                        <div className={`w-8 h-8 rounded-xl flex items-center justify-center text-[10px] font-black shrink-0 ${selectedAgents.has(idx) ? 'bg-[#16A34A] text-white' : 'bg-white/5 text-white/40'
                          }`}>
                          {(agent.username || 'A')[0]}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-[11px] font-bold text-white uppercase truncate">{agent.username}</div>
                          <div className="text-[9px] font-mono text-white/20 truncate uppercase">{agent.profession || 'UNKNOWN'}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="space-y-6">
                  <h4 className="text-[10px] font-mono font-black text-[#FAD4C0] uppercase tracking-widest italic">Global_Broadcast_Command</h4>
                  <div className="bg-[#0F1117] border border-white/10 rounded-2xl overflow-hidden focus-within:border-[#FAD4C0]/50 transition-colors">
                    <textarea
                      value={surveyQuestion}
                      onChange={e => setSurveyQuestion(e.target.value)}
                      placeholder="Define global query vector for selected nodes..."
                      rows={4}
                      className="w-full bg-transparent p-6 text-sm text-white placeholder:text-white/10 focus:outline-none resize-none"
                    />
                  </div>

                  <button
                    onClick={submitSurvey}
                    disabled={selectedAgents.size === 0 || !surveyQuestion.trim() || isSurveying}
                    className="w-full py-5 bg-[#16A34A] hover:bg-[#15af4c] text-white rounded-2xl font-mono font-black text-xs uppercase tracking-[0.2em] shadow-xl transition-all disabled:opacity-20 active:scale-95 flex items-center justify-center gap-4"
                  >
                    {isSurveying ? (
                      <span className="animate-pulse">Broadcasting_Signals...</span>
                    ) : (
                      <>
                        <span>Execute_Neural_Survey</span>
                        <span>→</span>
                      </>
                    )}
                  </button>
                </div>

                {surveyResults.length > 0 && (
                  <div className="space-y-6 pt-10 border-t border-white/5">
                    <h4 className="text-[10px] font-mono font-black text-[#FAD4C0] uppercase tracking-widest italic">{surveyResults.length}_RESPONSES_SYNCED</h4>
                    <div className="space-y-6">
                      {surveyResults.map((result, idx) => (
                        <div key={idx} className="bg-[#0F1117] border border-white/5 rounded-3xl p-8 space-y-4 group hover:border-white/10 transition-all">
                          <div className="flex items-center gap-4">
                            <div className="w-8 h-8 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-[10px] font-black text-blue-400">
                              {result.agent_name[0]}
                            </div>
                            <div>
                              <div className="text-[10px] font-bold text-white uppercase group-hover:text-blue-400 transition-colors">{result.agent_name}</div>
                              <div className="text-[8px] font-mono text-white/20 uppercase tracking-widest">{result.profession || 'CITIZEN_UNIT'}</div>
                            </div>
                          </div>
                          <div className="text-sm text-[#F5F0EB]/60 leading-relaxed italic border-l-2 border-white/5 pl-6 group-hover:border-blue-500/30 transition-all">
                            {result.answer}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

export default OntologyInteraction
