// API Types matching backend models

export interface Entity {
  id: string
  name: string
  type: 'GPE' | 'ORG' | 'PERSON' | 'EVENT' | 'TOPIC' | 'PRODUCT'
  domain: string
  attributes: Record<string, unknown>
  importance: number
  created_at: string
}

export interface EntityDetail extends Entity {
  relationships: Relationship[]
  recent_events: Event[]
}

export interface Event {
  id: string
  title: string
  summary: string
  domain: string
  source: string
  source_url: string | null
  published_at: string
  importance: number
  sentiment: number
  entities: string[]
  is_new: boolean
}

export interface Relationship {
  id: string
  source_id: string
  target_id: string
  type: string
  weight: number
}

export interface Signal {
  id: string
  name: string
  type: 'keyword' | 'entity' | 'pattern' | 'anomaly'
  status: 'active' | 'triggered' | 'paused'
  severity: 'low' | 'medium' | 'high' | 'critical'
  trigger_count: number
  last_triggered: string | null
  created_at: string
}

export interface SignalCreate {
  name: string
  type: Signal['type']
  severity?: Signal['severity']
  config?: Record<string, unknown>
}

export interface Query {
  id: string
  query: string
  response: string
  result?: string
  tokens_used: number
  created_at: string
}

export interface QueryRequest {
  query: string
  context?: Record<string, unknown>
}

export interface User {
  id: string
  email: string
  name: string | null
  tier: 'free' | 'basic' | 'professional' | 'enterprise'
  query_usage: number
  query_limit: number
}

export interface AuthResponse {
  access_token: string
  token_type: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface EventListResponse {
  events: Event[]
  total: number
  page: number
  page_size: number
}

export interface EntityListResponse {
  entities: Entity[]
  total: number
  page: number
  page_size: number
}

export interface AnalyticsOverview {
  total_events: number
  total_entities: number
  active_signals: number
  events_today: number
  queries_today?: number
  avg_sentiment: number
  domain_distribution: Record<string, number>
}

export interface DomainStats {
  domain: string
  count: number
  percentage: number
}

export interface TimeSeriesPoint {
  date: string
  count: number
}

export interface GraphData {
  nodes: Array<{
    uuid: string
    name: string
    labels: string[]
    type: string
    domain: string
    importance: number
    attributes: Record<string, any>
    summary?: string
    created_at?: string
  }>
  links: Array<{
    uuid: string
    source_node_uuid: string
    target_node_uuid: string
    source_node_name?: string
    target_node_name?: string
    name: string
    fact_type: string
    fact?: string
    weight: number
    attributes: Record<string, any>
    created_at?: string
    valid_at?: string
    invalid_at?: string
    episodes?: string[]
    metadata?: Record<string, any>
  }>
  edges?: Array<any>
  node_count: number
  edge_count: number
}

// MiroFish types
export interface OntologyEntityType {
  name: string
  description: string
  color?: string
}

export interface OntologyEdgeType {
  name: string
  description: string
  source_types: string[]
  target_types: string[]
}

export interface OntologyResponse {
  entity_types: OntologyEntityType[]
  edge_types: OntologyEdgeType[]
  source_text_preview?: string
}

export interface GraphBuildRequest {
  text: string
  entity_types?: string[]
  edge_types?: string[]
  provider?: string
  model?: string
}

export interface GraphBuildResponse {
  nodes_created: number
  edges_created: number
  message: string
}

export interface SimulationRequest {
  entity_ids: string[]
  scenario: string
  rounds?: number
  provider?: string
  model?: string
}

export interface SimulationResponse {
  simulation_id: string
  status: string
  rounds_completed: number
  results: Array<{
    round: number
    timestamp?: string
    events: Array<{
      actor: string
      action: string
      target: string
      impact: string
      significance: number
    }>
    relationship_changes: Array<{
      source: string
      target: string
      change: string
      reason: string
    }>
    analysis: string
  }>
}

export interface ReportRequest {
  entity_ids: string[]
  focus?: string
  provider?: string
  model?: string
}

export interface ReportResponse {
  report_id: string
  title: string
  sections: Array<{
    title: string
    content: string
  }>
  summary: string
}

export interface IngestionResult {
  total_fetched: number
  total_saved: number
  connector_status: Record<string, unknown>
  timestamp: string | null
}

export interface IngestionStatus {
  last_run: string | null
  connectors: Record<string, unknown>
  total_connectors: number
}

export interface GraphStats {
  total_nodes: number
  total_edges: number
  domains: Record<string, number>
  entity_types: Record<string, number>
  relationship_types: Record<string, number>
}

export interface ConnectorInfo {
  name: string
  tier: 'green' | 'yellow' | 'red'
  type: 'api' | 'rss' | 'scraper'
  domain: string
  status: 'ok' | 'error' | 'pending'
  last_fetch: string | null
  item_count: number
  error: string | null
  url?: string
}

export interface DetailedIngestionStatus {
  green: ConnectorInfo[]
  yellow: ConnectorInfo[]
  red: ConnectorInfo[]
  total_connectors: number
  total_events: number
  last_run: string | null
}

export interface SchedulerStatus {
  running: boolean
  interval_seconds: number
  last_run: string | null
  next_run: string | null
  events_last_run: number
}

export interface AIModel {
  id: string
  name: string
}

export interface AIProvider {
  id: string
  name: string
  models: AIModel[]
  available: boolean
}

export interface AIProvidersResponse {
  providers: AIProvider[]
  default: string
}
