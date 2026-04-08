import axios from 'axios'

// Ontology API - routes at /api/ (not /api/v1/)
const ontologyApi = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5001',
  timeout: 300000,
})

ontologyApi.interceptors.response.use(
  response => response,
  error => {
    console.error('[Ontology API Error]', error?.response?.data || error.message)
    return Promise.reject(error)
  }
)

// Retry helper — only retries on network/5xx errors, NOT 4xx (client errors)
export const requestWithRetry = async <T>(requestFn: () => Promise<T>, maxRetries = 3, delay = 1000): Promise<T> => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await requestFn()
    } catch (error: any) {
      const status = error?.response?.status
      // Don't retry 4xx errors — they're client errors that won't change on retry
      if (status && status >= 400 && status < 500) throw error
      if (i === maxRetries - 1) throw error
      console.warn(`Request failed (${status || 'network'}), retrying (${i + 1}/${maxRetries})...`)
      await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)))
    }
  }
  throw new Error('Max retries reached')
}

// ========== Graph APIs ==========
export const graphApi = {
  generateOntology: (formData: FormData) =>
    ontologyApi.post('/api/graph/ontology/generate', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 600000,
    }),

  buildGraph: (data: { project_id: string; chunk_size?: number; chunk_overlap?: number }) =>
    ontologyApi.post('/api/graph/build', data),

  getTaskStatus: (taskId: string) =>
    ontologyApi.get(`/api/graph/task/${taskId}`),

  getGraphData: (graphId: string) =>
    ontologyApi.get(`/api/graph/data/${graphId}`),

  getProject: (projectId: string) =>
    ontologyApi.get(`/api/graph/project/${projectId}`),

  getProjectState: (projectId: string) =>
    ontologyApi.get(`/api/graph/project/${projectId}/state`),

  listProjects: () =>
    ontologyApi.get('/api/graph/project/list'),

  deleteProject: (projectId: string) =>
    ontologyApi.delete(`/api/graph/project/${projectId}`),

  resetProject: (projectId: string) =>
    ontologyApi.post(`/api/graph/project/${projectId}/reset`),

  listTasks: () =>
    ontologyApi.get('/api/graph/tasks'),
}

// ========== Simulation APIs ==========
export const simulationApi = {
  create: (data: { project_id: string; graph_id: string; enable_twitter?: boolean; enable_reddit?: boolean; max_rounds?: number }) =>
    ontologyApi.post('/api/simulation/create', data),

  prepare: (data: { simulation_id: string; graph_id?: string; platform?: string; entity_types?: string[] }) =>
    ontologyApi.post('/api/simulation/prepare', data),

  getPrepareStatus: (data: { task_id?: string; simulation_id?: string }) =>
    ontologyApi.post('/api/simulation/prepare/status', data),

  get: (simulationId: string) =>
    ontologyApi.get(`/api/simulation/${simulationId}`),

  getProfiles: (simulationId: string, platform: string = 'reddit') =>
    ontologyApi.get(`/api/simulation/${simulationId}/profiles`, { params: { platform } }),

  getConfig: (simulationId: string) =>
    ontologyApi.get(`/api/simulation/${simulationId}/config`),

  list: (projectId?: string) =>
    ontologyApi.get('/api/simulation/list', { params: projectId ? { project_id: projectId } : {} }),

  start: (data: { simulation_id: string; max_rounds?: number; force?: boolean; platform?: string; enable_graph_memory_update?: boolean }) =>
    ontologyApi.post('/api/simulation/start', data),

  stop: (data: { simulation_id: string }) =>
    ontologyApi.post('/api/simulation/stop', data),

  getRunStatus: (simulationId: string) =>
    ontologyApi.get(`/api/simulation/${simulationId}/run-status`),

  getPosts: (simulationId: string, params?: { platform?: string; limit?: number }) =>
    ontologyApi.get(`/api/simulation/${simulationId}/posts`, { params }),

  getTimeline: (simulationId: string) =>
    ontologyApi.get(`/api/simulation/${simulationId}/timeline`),

  getAgentStats: (simulationId: string) =>
    ontologyApi.get(`/api/simulation/${simulationId}/agent-stats`),

  getActions: (simulationId: string, limit: number = 50) =>
    ontologyApi.get(`/api/simulation/${simulationId}/actions`, { params: { limit } }),

  getRunStatusDetail: (simulationId: string) =>
    ontologyApi.get(`/api/simulation/${simulationId}/run-status/detail`),

  closeEnv: (data: { simulation_id: string }) =>
    ontologyApi.post('/api/simulation/close-env', data),

  getEnvStatus: (data: { simulation_id: string }) =>
    ontologyApi.post('/api/simulation/env-status', data),

  interviewAgents: (data: { simulation_id: string; agent_ids: string[]; questions: string[] }) =>
    ontologyApi.post('/api/simulation/interview/batch', data),

  getHistory: () =>
    ontologyApi.get('/api/simulation/history'),
}

// ========== Report APIs ==========
export const reportApi = {
  generate: (data: { simulation_id: string; project_id?: string; graph_id?: string }) =>
    ontologyApi.post('/api/report/generate', data),

  getStatus: (params?: { task_id?: string }) =>
    ontologyApi.get('/api/report/generate/status', { params }),

  get: (reportId: string) =>
    ontologyApi.get(`/api/report/${reportId}`),

  chat: (data: { report_id: string; message: string; history?: Array<{ role: string; content: string }> }) =>
    ontologyApi.post('/api/report/chat', data),

  getAgentLog: (reportId: string, fromLine?: number) =>
    ontologyApi.get(`/api/report/${reportId}/agent-log`, { params: fromLine ? { from_line: fromLine } : {} }),

  getConsoleLog: (reportId: string, fromLine?: number) =>
    ontologyApi.get(`/api/report/${reportId}/console-log`, { params: fromLine ? { from_line: fromLine } : {} }),
}
