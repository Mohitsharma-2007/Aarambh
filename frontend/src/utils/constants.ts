/// <reference types="vite/client" />
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001'

export const APP_NAME = 'AARAMBH'
export const APP_VERSION = '2.0.0'

export const DOMAINS = [
  'geopolitics',
  'economics',
  'defense',
  'technology',
  'climate',
  'society',
] as const

export const ENTITY_TYPES = [
  'GPE',      // Geopolitical Entity
  'ORG',      // Organization
  'PERSON',   // Person
  'EVENT',    // Event
  'TOPIC',    // Topic/Theme
  'PRODUCT',  // Product/Weapon System
] as const

export const SENTIMENT_THRESHOLDS = {
  positive: 0.3,
  negative: -0.3,
} as const

export const IMPORTANCE_LEVELS = {
  critical: 9,
  high: 7,
  medium: 5,
  low: 3,
} as const

export const QUERY_LIMITS = {
  free: 100,
  basic: 1000,
  professional: 10000,
  enterprise: 100000,
} as const

export const CACHE_KEYS = {
  FEED: 'aarambh_feed',
  ENTITIES: 'aarambh_entities',
  GRAPH: 'aarambh_graph',
  USER: 'aarambh_user',
} as const

export const STORAGE_KEYS = {
  THEME: 'aarambh_theme',
  SIDEBAR: 'aarambh_sidebar',
  RECENT_QUERIES: 'aarambh_recent_queries',
} as const
