import { create } from 'zustand'
import type { Domain } from '@/constants/domains'

export type { Domain }

export interface IntelligenceEvent {
  id: string
  title: string
  summary: string
  domain: Domain
  source: string
  sourceUrl: string
  publishedAt: string
  importance: number
  entities: string[]
  sentiment: number
  isNew?: boolean
}

interface FeedStore {
  events: IntelligenceEvent[]
  domainFilter: Domain | 'all'
  isConnected: boolean
  totalEvents: number
  
  // Actions
  addEvent: (event: IntelligenceEvent) => void
  addEvents: (events: IntelligenceEvent[]) => void
  setDomainFilter: (domain: Domain | 'all') => void
  setConnected: (connected: boolean) => void
  clearEvents: () => void
}

export const useFeedStore = create<FeedStore>((set) => ({
  events: [],
  domainFilter: 'all',
  isConnected: false,
  totalEvents: 0,

  addEvent: (event) => set((state) => ({
    events: [event, ...state.events].slice(0, 1000),
    totalEvents: state.totalEvents + 1,
  })),

  addEvents: (newEvents) => set((state) => ({
    events: [...newEvents, ...state.events].slice(0, 1000),
    totalEvents: state.totalEvents + newEvents.length,
  })),

  setDomainFilter: (domain) => set({ domainFilter: domain }),
  
  setConnected: (connected) => set({ isConnected: connected }),
  
  clearEvents: () => set({ events: [], totalEvents: 0 }),
}))
