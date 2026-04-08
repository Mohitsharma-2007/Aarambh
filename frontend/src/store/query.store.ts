import { create } from 'zustand'

export type QueryMode = 'quick' | 'full' | 'multi-model'

export interface QueryResponse {
  id: string
  query: string
  mode: QueryMode
  content: string
  model: string
  confidence: number
  sources: QuerySource[]
  entities: string[]
  tokens: number
  latency_ms: number
  timestamp: number
  isStreaming?: boolean
}

export interface QuerySource {
  id: string
  title: string
  url: string
  source: string
  relevance: number
}

interface QueryStore {
  // State
  history: QueryResponse[]
  currentQuery: string
  currentResponse: QueryResponse | null
  isQuerying: boolean
  mode: QueryMode
  suggestions: string[]
  error: string | null

  // Actions
  setCurrentQuery: (query: string) => void
  setMode: (mode: QueryMode) => void
  submitQuery: (query: string, mode: QueryMode) => Promise<void>
  addToHistory: (response: QueryResponse) => void
  clearHistory: () => void
  clearCurrentResponse: () => void
  setSuggestions: (suggestions: string[]) => void
  setError: (error: string | null) => void
  streamResponse: (content: string) => void
}

export const useQueryStore = create<QueryStore>((set, get) => ({
  // Initial state
  history: [],
  currentQuery: '',
  currentResponse: null,
  isQuerying: false,
  mode: 'quick',
  suggestions: [
    'What is the current India-China border situation?',
    'Analyze recent BRICS expansion implications',
    'Track defense budget changes in South Asia',
    'Map key technology partnerships involving India',
    'Summarize recent climate policy developments',
    'Identify emerging geopolitical risks in Indo-Pacific',
  ],
  error: null,

  // Actions
  setCurrentQuery: (query) => set({ currentQuery: query }),
  setMode: (mode) => set({ mode }),

  submitQuery: async (query, mode) => {
    set({ isQuerying: true, error: null, currentQuery: query })

    const response: QueryResponse = {
      id: `query_${Date.now()}`,
      query,
      mode,
      content: '',
      model: '',
      confidence: 0,
      sources: [],
      entities: [],
      tokens: 0,
      latency_ms: 0,
      timestamp: Date.now(),
      isStreaming: true,
    }

    set({ currentResponse: response })

    try {
      const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001/api/v1'
      const endpoint = mode === 'quick' ? '/query/quick' :
                       mode === 'full' ? '/query/full' : '/query/multi-model'

      const res = await fetch(`${apiBase}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, mode }),
      })

      if (!res.ok) throw new Error(`Query failed: ${res.status}`)

      const data = await res.json()

      const finalResponse: QueryResponse = {
        ...response,
        content: data.content || data.response || '',
        model: data.model || 'unknown',
        confidence: data.confidence || 0.85,
        sources: data.sources || [],
        entities: data.entities || [],
        tokens: data.tokens || 0,
        latency_ms: data.latency_ms || 0,
        isStreaming: false,
      }

      set({ currentResponse: finalResponse, isQuerying: false })
      get().addToHistory(finalResponse)
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Query failed'
      set({ error: errorMessage, isQuerying: false })
    }
  },

  addToHistory: (response) => set((state) => ({
    history: [response, ...state.history].slice(0, 100),
  })),

  clearHistory: () => set({ history: [] }),
  clearCurrentResponse: () => set({ currentResponse: null }),
  setSuggestions: (suggestions) => set({ suggestions }),
  setError: (error) => set({ error }),

  streamResponse: (content) => set((state) => ({
    currentResponse: state.currentResponse
      ? { ...state.currentResponse, content }
      : null,
  })),
}))
