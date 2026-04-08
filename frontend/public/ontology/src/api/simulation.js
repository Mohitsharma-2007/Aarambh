import service, { requestWithRetry } from './index'

/**
 * CreateSimulation
 * @param {Object} data - { project_id, graph_id?, enable_twitter?, enable_reddit? }
 */
export const createSimulation = (data) => {
  return requestWithRetry(() => service.post('/api/simulation/create', data), 3, 1000)
}

/**
 * PrepareSimulationEnvironment（Async Task）
 * @param {Object} data - { simulation_id, entity_types?, use_llm_for_profiles?, parallel_profile_count?, force_regenerate? }
 */
export const prepareSimulation = (data) => {
  return requestWithRetry(() => service.post('/api/simulation/prepare', data), 3, 1000)
}

/**
 * QueryPrepareTaskProgress
 * @param {Object} data - { task_id?, simulation_id? }
 */
export const getPrepareStatus = (data) => {
  return service.post('/api/simulation/prepare/status', data)
}

/**
 * GetSimulationStatus
 * @param {string} simulationId
 */
export const getSimulation = (simulationId) => {
  return service.get(`/api/simulation/${simulationId}`)
}

/**
 * GetSimulation Agent Profiles
 * @param {string} simulationId
 * @param {string} platform - 'reddit' | 'twitter'
 */
export const getSimulationProfiles = (simulationId, platform = 'reddit') => {
  return service.get(`/api/simulation/${simulationId}/profiles`, { params: { platform } })
}

/**
 * Real-timeGetGenerating Agent Profiles
 * @param {string} simulationId
 * @param {string} platform - 'reddit' | 'twitter'
 */
export const getSimulationProfilesRealtime = (simulationId, platform = 'reddit') => {
  return service.get(`/api/simulation/${simulationId}/profiles/realtime`, { params: { platform } })
}

/**
 * StartSimulation
 * @param {string} simulationId
 * @param {Object} data - { rounds?, platform?, enable_interview? }
 */
export const startSimulation = (simulationId, data) => {
  return service.post(`/api/simulation/${simulationId}/start`, data)
}

/**
 * GetSimulationStatus（Real-time）
 * @param {string} simulationId
 */
export const getSimulationStatus = (simulationId) => {
  return service.get(`/api/simulation/${simulationId}/status`)
}

/**
 * StopSimulation
 * @param {string} simulationId
 */
export const stopSimulation = (simulationId) => {
  return service.post(`/api/simulation/${simulationId}/stop`)
}

/**
 * GetInterviewHistory
 * @param {string} simulationId
 * @param {string} platform - 'reddit' | 'twitter'
 */
export const getInterviewHistory = (simulationId, platform = 'reddit') => {
  return service.get(`/api/simulation/${simulationId}/interview`, { params: { platform } })
}

/**
 * SendInterviewMessage
 * @param {string} simulationId
 * @param {Object} data - { agent_id, message, platform }
 */
export const sendInterviewMessage = (simulationId, data) => {
  return service.post(`/api/simulation/${simulationId}/interview`, data)
}

/**
 * GetEntityDetailInformation
 * @param {string} graphId
 * @param {string} entityUuid
 */
export const getEntityDetail = (graphId, entityUuid) => {
  return service.get(`/api/simulation/entities/${graphId}/${entityUuid}`)
}

/**
 * GetGraphAllEntities
 * @param {string} graphId
 * @param {Object} params - { entity_types?, enrich? }
 */
export const getGraphEntities = (graphId, params = {}) => {
  return service.get(`/api/simulation/entities/${graphId}`, { params })
}
