<template>
  <div class="main-view">
    <!-- Header -->
    <header class="app-header">
      <div class="header-left">
        <div class="brand" @click="router.push('/')">aarambh</div>
      </div>
      
      <div class="header-center">
        <div class="view-switcher">
          <button 
            v-for="mode in ['graph', 'split', 'workbench']" 
            :key="mode"
            class="switch-btn"
            :class="{ active: viewMode === mode }"
            @click="viewMode = mode"
          >
            {{ { graph: 'å›¾è°±', split: 'åŒæ ', workbench: 'å·¥ä½œå°' }[mode] }}
          </button>
        </div>
      </div>

      <div class="header-right">
        <div class="workflow-step">
          <span class="step-num">Step 2/5</span>
          <span class="step-name">çŽ¯å¢ƒæ­å»º</span>
        </div>
        <div class="step-divider"></div>
        <span class="status-indicator" :class="statusClass">
          <span class="dot"></span>
          {{ statusText }}
        </span>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="content-area">
      <!-- Left Panel: Graph -->
      <div class="panel-wrapper left" :style="leftPanelStyle">
        <GraphPanel 
          :graphData="graphData"
          :loading="graphLoading"
          :currentPhase="2"
          @refresh="refreshGraph"
          @toggle-maximize="toggleMaximize('graph')"
        />
      </div>

      <!-- Right Panel: Step2 çŽ¯å¢ƒæ­å»º -->
      <div class="panel-wrapper right" :style="rightPanelStyle">
        <Step2EnvSetup
          :simulationId="currentSimulationId"
          :projectData="projectData"
          :graphData="graphData"
          :systemLogs="systemLogs"
          @go-back="handleGoBack"
          @next-step="handleNextStep"
          @add-log="addLog"
          @update-status="updateStatus"
        />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import GraphPanel from '../components/GraphPanel.vue'
import Step2EnvSetup from '../components/Step2EnvSetup.vue'
import { getProject, getGraphData } from '../api/graph'
import { getSimulation, stopSimulation, getEnvStatus, closeSimulationEnv } from '../api/simulation'

const route = useRoute()
const router = useRouter()

// Props
const props = defineProps({
  simulationId: String
})

// Layout State
const viewMode = ref('split')

// Data State
const currentSimulationId = ref(route.params.simulationId)
const projectData = ref(null)
const graphData = ref(null)
const graphLoading = ref(false)
const systemLogs = ref([])
const currentStatus = ref('processing') // processing | completed | error

// --- Computed Layout Styles ---
const leftPanelStyle = computed(() => {
  if (viewMode.value === 'graph') return { width: '100%', opacity: 1, transform: 'translateX(0)' }
  if (viewMode.value === 'workbench') return { width: '0%', opacity: 0, transform: 'translateX(-20px)' }
  return { width: '50%', opacity: 1, transform: 'translateX(0)' }
})

const rightPanelStyle = computed(() => {
  if (viewMode.value === 'workbench') return { width: '100%', opacity: 1, transform: 'translateX(0)' }
  if (viewMode.value === 'graph') return { width: '0%', opacity: 0, transform: 'translateX(20px)' }
  return { width: '50%', opacity: 1, transform: 'translateX(0)' }
})

// --- Status Computed ---
const statusClass = computed(() => {
  return currentStatus.value
})

const statusText = computed(() => {
  if (currentStatus.value === 'error') return 'Error'
  if (currentStatus.value === 'completed') return 'Ready'
  return 'Preparing'
})

// --- Helpers ---
const addLog = (msg) => {
  const time = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) + '.' + new Date().getMilliseconds().toString().padStart(3, '0')
  systemLogs.value.push({ time, msg })
  if (systemLogs.value.length > 100) {
    systemLogs.value.shift()
  }
}

const updateStatus = (status) => {
  currentStatus.value = status
}

// --- Layout Methods ---
const toggleMaximize = (target) => {
  if (viewMode.value === target) {
    viewMode.value = 'split'
  } else {
    viewMode.value = target
  }
}

const handleGoBack = () => {
  // è¿”å›žåˆ° process é¡µé¢
  if (projectData.value?.project_id) {
    router.push({ name: 'Process', params: { projectId: projectData.value.project_id } })
  } else {
    router.push('/')
  }
}

const handleNextStep = (params = {}) => {
  addLog('è¿›å…¥ Step 3: å¼€å§‹æ¨¡æ‹Ÿ')
  
  // è®°å½•æ¨¡æ‹Ÿè½®æ•°é…ç½®
  if (params.maxRounds) {
    addLog(`è‡ªå®šä¹‰æ¨¡æ‹Ÿè½®æ•°: ${params.maxRounds} è½®`)
  } else {
    addLog('ä½¿ç”¨è‡ªåŠ¨é…ç½®çš„æ¨¡æ‹Ÿè½®æ•°')
  }
  
  // æž„å»ºè·¯ç”±å‚æ•°
  const routeParams = {
    name: 'SimulationRun',
    params: { simulationId: currentSimulationId.value }
  }
  
  // å¦‚æžœæœ‰è‡ªå®šä¹‰è½®æ•°ï¼Œé€šè¿‡ query å‚æ•°ä¼ é€’
  if (params.maxRounds) {
    routeParams.query = { maxRounds: params.maxRounds }
  }
  
  // è·³è½¬åˆ° Step 3 é¡µé¢
  router.push(routeParams)
}

// --- Data Logic ---

/**
 * æ£€æŸ¥å¹¶å…³é—­æ­£åœ¨è¿è¡Œçš„æ¨¡æ‹Ÿ
 * å½“ç”¨æˆ·ä»Ž Step 3 è¿”å›žåˆ° Step 2 æ—¶ï¼Œé»˜è®¤ç”¨æˆ·è¦é€€å‡ºæ¨¡æ‹Ÿ
 */
const checkAndStopRunningSimulation = async () => {
  if (!currentSimulationId.value) return
  
  try {
    // å…ˆæ£€æŸ¥æ¨¡æ‹ŸçŽ¯å¢ƒæ˜¯å¦å­˜æ´»
    const envStatusRes = await getEnvStatus({ simulation_id: currentSimulationId.value })
    
    if (envStatusRes.success && envStatusRes.data?.env_alive) {
      addLog('æ£€æµ‹åˆ°æ¨¡æ‹ŸçŽ¯å¢ƒæ­£åœ¨è¿è¡Œï¼Œæ­£åœ¨å…³é—­...')
      
      // å°è¯•ä¼˜é›…å…³é—­æ¨¡æ‹ŸçŽ¯å¢ƒ
      try {
        const closeRes = await closeSimulationEnv({ 
          simulation_id: currentSimulationId.value,
          timeout: 10  // 10ç§’è¶…æ—¶
        })
        
        if (closeRes.success) {
          addLog('âœ“ æ¨¡æ‹ŸçŽ¯å¢ƒå·²å…³é—­')
        } else {
          addLog(`å…³é—­æ¨¡æ‹ŸçŽ¯å¢ƒå¤±è´¥: ${closeRes.error || 'æœªçŸ¥é”™è¯¯'}`)
          // å¦‚æžœä¼˜é›…å…³é—­å¤±è´¥ï¼Œå°è¯•å¼ºåˆ¶åœæ­¢
          await forceStopSimulation()
        }
      } catch (closeErr) {
        addLog(`å…³é—­æ¨¡æ‹ŸçŽ¯å¢ƒå¼‚å¸¸: ${closeErr.message}`)
        // å¦‚æžœä¼˜é›…å…³é—­å¼‚å¸¸ï¼Œå°è¯•å¼ºåˆ¶åœæ­¢
        await forceStopSimulation()
      }
    } else {
      // çŽ¯å¢ƒæœªè¿è¡Œï¼Œä½†å¯èƒ½è¿›ç¨‹è¿˜åœ¨ï¼Œæ£€æŸ¥æ¨¡æ‹ŸçŠ¶æ€
      const simRes = await getSimulation(currentSimulationId.value)
      if (simRes.success && simRes.data?.status === 'running') {
        addLog('æ£€æµ‹åˆ°æ¨¡æ‹ŸçŠ¶æ€ä¸ºè¿è¡Œä¸­ï¼Œæ­£åœ¨åœæ­¢...')
        await forceStopSimulation()
      }
    }
  } catch (err) {
    // æ£€æŸ¥çŽ¯å¢ƒçŠ¶æ€å¤±è´¥ä¸å½±å“åŽç»­æµç¨‹
    console.warn('æ£€æŸ¥æ¨¡æ‹ŸçŠ¶æ€å¤±è´¥:', err)
  }
}

/**
 * å¼ºåˆ¶åœæ­¢æ¨¡æ‹Ÿ
 */
const forceStopSimulation = async () => {
  try {
    const stopRes = await stopSimulation({ simulation_id: currentSimulationId.value })
    if (stopRes.success) {
      addLog('âœ“ æ¨¡æ‹Ÿå·²å¼ºåˆ¶åœæ­¢')
    } else {
      addLog(`å¼ºåˆ¶åœæ­¢æ¨¡æ‹Ÿå¤±è´¥: ${stopRes.error || 'æœªçŸ¥é”™è¯¯'}`)
    }
  } catch (err) {
    addLog(`å¼ºåˆ¶åœæ­¢æ¨¡æ‹Ÿå¼‚å¸¸: ${err.message}`)
  }
}

const loadSimulationData = async () => {
  try {
    addLog(`åŠ è½½æ¨¡æ‹Ÿæ•°æ®: ${currentSimulationId.value}`)
    
    // èŽ·å– simulation ä¿¡æ¯
    const simRes = await getSimulation(currentSimulationId.value)
    if (simRes.success && simRes.data) {
      const simData = simRes.data
      
      // èŽ·å– project ä¿¡æ¯
      if (simData.project_id) {
        const projRes = await getProject(simData.project_id)
        if (projRes.success && projRes.data) {
          projectData.value = projRes.data
          addLog(`é¡¹ç›®åŠ è½½æˆåŠŸ: ${projRes.data.project_id}`)
          
          // èŽ·å– graph æ•°æ®
          if (projRes.data.graph_id) {
            await loadGraph(projRes.data.graph_id)
          }
        }
      }
    } else {
      addLog(`åŠ è½½æ¨¡æ‹Ÿæ•°æ®å¤±è´¥: ${simRes.error || 'æœªçŸ¥é”™è¯¯'}`)
    }
  } catch (err) {
    addLog(`åŠ è½½å¼‚å¸¸: ${err.message}`)
  }
}

const loadGraph = async (graphId) => {
  graphLoading.value = true
  try {
    const res = await getGraphData(graphId)
    if (res.success) {
      graphData.value = res.data
      addLog('å›¾è°±æ•°æ®åŠ è½½æˆåŠŸ')
    }
  } catch (err) {
    addLog(`å›¾è°±åŠ è½½å¤±è´¥: ${err.message}`)
  } finally {
    graphLoading.value = false
  }
}

const refreshGraph = () => {
  if (projectData.value?.graph_id) {
    loadGraph(projectData.value.graph_id)
  }
}

onMounted(async () => {
  addLog('SimulationView åˆå§‹åŒ–')
  
  // æ£€æŸ¥å¹¶å…³é—­æ­£åœ¨è¿è¡Œçš„æ¨¡æ‹Ÿï¼ˆç”¨æˆ·ä»Ž Step 3 è¿”å›žæ—¶ï¼‰
  await checkAndStopRunningSimulation()
  
  // åŠ è½½æ¨¡æ‹Ÿæ•°æ®
  loadSimulationData()
})
</script>

<style scoped>
.main-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #FFF;
  overflow: hidden;
  font-family: 'Space Grotesk', 'Noto Sans SC', system-ui, sans-serif;
}

/* Header */
.app-header {
  height: 60px;
  border-bottom: 1px solid #EAEAEA;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: #FFF;
  z-index: 100;
  position: relative;
}

.brand {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 800;
  font-size: 18px;
  letter-spacing: 1px;
  cursor: pointer;
}

.header-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.view-switcher {
  display: flex;
  background: #F5F5F5;
  padding: 4px;
  border-radius: 6px;
  gap: 4px;
}

.switch-btn {
  border: none;
  background: transparent;
  padding: 6px 16px;
  font-size: 12px;
  font-weight: 600;
  color: #666;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.switch-btn.active {
  background: #FFF;
  color: #000;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.workflow-step {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.step-num {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  color: #999;
}

.step-name {
  font-weight: 700;
  color: #000;
}

.step-divider {
  width: 1px;
  height: 14px;
  background-color: #E0E0E0;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #CCC;
}

.status-indicator.processing .dot { background: #FF5722; animation: pulse 1s infinite; }
.status-indicator.completed .dot { background: #4CAF50; }
.status-indicator.error .dot { background: #F44336; }

@keyframes pulse { 50% { opacity: 0.5; } }

/* Content */
.content-area {
  flex: 1;
  display: flex;
  position: relative;
  overflow: hidden;
}

.panel-wrapper {
  height: 100%;
  overflow: hidden;
  transition: width 0.4s cubic-bezier(0.25, 0.8, 0.25, 1), opacity 0.3s ease, transform 0.3s ease;
  will-change: width, opacity, transform;
}

.panel-wrapper.left {
  border-right: 1px solid #EAEAEA;
}
</style>

