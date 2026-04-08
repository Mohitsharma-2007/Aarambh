import { create } from 'zustand'

export type ResearchDepth = 'quick' | 'standard' | 'deep'
export type ResearchStatus = 'pending' | 'processing' | 'completed' | 'failed'

export interface ResearchStep {
  id: string
  name: string
  status: 'pending' | 'running' | 'done' | 'failed'
  message?: string
  data?: Record<string, unknown>
}

export interface Citation {
  id: string
  title: string
  url: string
  source: string
  published_at: string
}

export interface ResearchReport {
  id: string
  topic: string
  depth: ResearchDepth
  status: ResearchStatus
  content: string
  citations: Citation[]
  entities: string[]
  steps: ResearchStep[]
  word_count: number
  sources_used: number
  processing_time_ms: number
  created_at: string
  completed_at?: string
}

interface ResearchStore {
  // State
  reports: ResearchReport[]
  currentReport: ResearchReport | null
  isResearching: boolean
  currentTopic: string
  currentDepth: ResearchDepth
  steps: ResearchStep[]
  error: string | null

  // Actions
  setCurrentTopic: (topic: string) => void
  setCurrentDepth: (depth: ResearchDepth) => void
  startResearch: (topic: string, depth: ResearchDepth) => Promise<void>
  updateStep: (stepId: string, updates: Partial<ResearchStep>) => void
  addReport: (report: ResearchReport) => void
  deleteReport: (id: string) => void
  loadReport: (id: string) => void
  clearCurrentReport: () => void
  setError: (error: string | null) => void
}

const RESEARCH_STEPS: ResearchStep[] = [
  { id: 'decompose', name: 'Topic Decomposition', status: 'pending' },
  { id: 'graph', name: 'Graph Query', status: 'pending' },
  { id: 'web_search', name: 'Web Search', status: 'pending' },
  { id: 'documents', name: 'Document Retrieval', status: 'pending' },
  { id: 'entities', name: 'Entity Extraction', status: 'pending' },
  { id: 'citations', name: 'Citation Building', status: 'pending' },
  { id: 'synthesis', name: 'AI Synthesis', status: 'pending' },
  { id: 'report', name: 'Report Generation', status: 'pending' },
]

export const useResearchStore = create<ResearchStore>((set, get) => ({
  // Initial state
  reports: [],
  currentReport: null,
  isResearching: false,
  currentTopic: '',
  currentDepth: 'standard',
  steps: [...RESEARCH_STEPS],
  error: null,

  // Actions
  setCurrentTopic: (topic) => set({ currentTopic: topic }),
  setCurrentDepth: (depth) => set({ currentDepth: depth }),

  startResearch: async (topic, depth) => {
    set({
      isResearching: true,
      error: null,
      currentTopic: topic,
      currentDepth: depth,
      steps: RESEARCH_STEPS.map(s => ({ ...s, status: 'pending' })),
    })

    try {
      const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001/api/v1'

      // Start research job
      const startRes = await fetch(`${apiBase}/research/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, depth }),
      })

      if (!startRes.ok) throw new Error('Failed to start research')

      const { job_id } = await startRes.json()

      // Poll for results with SSE-like updates
      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await fetch(`${apiBase}/research/${job_id}`)
          const status = await statusRes.json()

          // Update steps
          if (status.steps) {
            status.steps.forEach((step: ResearchStep) => {
              get().updateStep(step.id, step)
            })
          }

          if (status.status === 'completed') {
            clearInterval(pollInterval)

            const report: ResearchReport = {
              id: job_id,
              topic,
              depth,
              status: 'completed',
              content: status.report?.content || '',
              citations: status.report?.citations || [],
              entities: status.report?.entities || [],
              steps: get().steps,
              word_count: status.report?.word_count || 0,
              sources_used: status.report?.sources_used || 0,
              processing_time_ms: status.processing_time_ms || 0,
              created_at: new Date().toISOString(),
              completed_at: new Date().toISOString(),
            }

            set({ currentReport: report, isResearching: false })
            get().addReport(report)
          } else if (status.status === 'failed') {
            clearInterval(pollInterval)
            set({ isResearching: false, error: status.error || 'Research failed' })
          }
        } catch (e) {
          console.error('Polling error:', e)
        }
      }, 2000)

      // Store interval for cleanup
      setTimeout(() => clearInterval(pollInterval), 600000) // 10 min max
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Research failed'
      set({ error: errorMessage, isResearching: false })
    }
  },

  updateStep: (stepId, updates) => set((state) => ({
    steps: state.steps.map((s) =>
      s.id === stepId ? { ...s, ...updates } : s
    ),
  })),

  addReport: (report) => set((state) => ({
    reports: [report, ...state.reports].slice(0, 50),
  })),

  deleteReport: (id) => set((state) => ({
    reports: state.reports.filter((r) => r.id !== id),
    currentReport: state.currentReport?.id === id ? null : state.currentReport,
  })),

  loadReport: (id) => {
    const report = get().reports.find((r) => r.id === id)
    if (report) set({ currentReport: report })
  },

  clearCurrentReport: () => set({ currentReport: null }),
  setError: (error) => set({ error }),
}))
