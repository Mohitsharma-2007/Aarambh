import React, { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import * as d3 from 'd3'

interface AgentProfile {
  agent_id: string
  username: string
  bio: string
}

interface SimulationConfig {
  simulation_id: string
  config: {
    enable_twitter: boolean
    enable_reddit: boolean
    max_rounds: number
  }
  time_config?: { total_simulation_hours: number; minutes_per_round: number }
  platform_config?: Record<string, { enabled: boolean }>
}

export const OntologySimulation: React.FC = () => {
  const { projectId } = useParams()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const simulationId = searchParams.get('simId') || ''
  const graphId = searchParams.get('graphId') || ''

  const [simulation, setSimulation] = useState<any>(null)
  const [profiles, setProfiles] = useState<{ twitter: AgentProfile[], reddit: AgentProfile[] }>({ twitter: [], reddit: [] })
  const [config, setConfig] = useState<SimulationConfig | null>(null)
  const [maxRounds, setMaxRounds] = useState(10)
  const [loading, setLoading] = useState(true)
  const [starting, setStarting] = useState(false)
  const [activeTab, setActiveTab] = useState<'twitter' | 'reddit'>('twitter')

  useEffect(() => {
    if (simulationId) loadSimulation()
    else setLoading(false)
  }, [simulationId])

  const loadSimulation = async () => {
    try {
      const [simRes, twitterRes, redditRes, configRes] = await Promise.all([
        fetch(`http://localhost:5001/api/simulation/${simulationId}`),
        fetch(`http://localhost:5001/api/simulation/${simulationId}/profiles?platform=twitter`),
        fetch(`http://localhost:5001/api/simulation/${simulationId}/profiles?platform=reddit`),
        fetch(`http://localhost:5001/api/simulation/${simulationId}/config`),
      ])

      const [simData, twitterData, redditData, configData] = await Promise.all([
        simRes.json(), twitterRes.json(), redditRes.json(), configRes.json()
      ])

      if (simData.success) setSimulation(simData.data)
      setProfiles({ twitter: twitterData.data || [], reddit: redditData.data || [] })
      if (configData.success) {
        setConfig(configData.data)
        setMaxRounds(configData.data?.config?.max_rounds || 10)
      }
    } catch (err) {
      console.error('Failed to load simulation:', err)
    } finally {
      setLoading(false)
    }
  }

  const startSimulation = async () => {
    if (!simulationId) return
    setStarting(true)

    try {
      const res = await fetch('http://localhost:5001/api/simulation/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ simulation_id: simulationId, max_rounds: maxRounds }),
      })
      const data = await res.json()

      if (data.success) {
        navigate(`/simulation/run/${simulationId}?maxRounds=${maxRounds}&projectId=${projectId}&graphId=${graphId}`)
      }
    } catch (err) {
      console.error('Failed to start:', err)
    } finally {
      setStarting(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-gray-200">
      {/* Header */}
      <div className="border-b border-gray-800 bg-[#0d0d14]">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => navigate(-1)} className="text-gray-500 hover:text-gray-300 text-sm font-mono">&larr; Back</button>
            <div className="h-4 w-px bg-gray-700" />
            <h1 className="text-sm font-mono text-amber-400">Simulation Environment</h1>
          </div>
          <div className="flex items-center gap-2 text-xs font-mono text-gray-500">
            <span className={`w-2 h-2 rounded-full ${simulation?.status === 'prepared' ? 'bg-green-400' : 'bg-yellow-400'}`} />
            {simulation?.status || 'Loading'}
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Configuration */}
          <div className="bg-[#111118] border border-gray-800 rounded-lg p-4">
            <h3 className="text-sm font-mono text-amber-400 mb-4">Configuration</h3>

            <div className="space-y-4">
              <div>
                <label className="text-xs text-gray-500 font-mono block mb-1">Max Rounds</label>
                <input
                  type="number"
                  value={maxRounds}
                  onChange={e => setMaxRounds(parseInt(e.target.value) || 10)}
                  min={1}
                  max={100}
                  className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm font-mono text-gray-200 focus:border-amber-500 focus:outline-none"
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-gray-400">Twitter</span>
                  <span className={config?.config?.enable_twitter ? 'text-green-400' : 'text-gray-600'}>
                    {config?.config?.enable_twitter ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-gray-400">Reddit</span>
                  <span className={config?.config?.enable_reddit ? 'text-green-400' : 'text-gray-600'}>
                    {config?.config?.enable_reddit ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
              </div>

              {config?.time_config && (
                <div className="p-2 bg-gray-900/50 rounded space-y-1">
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-gray-500">Sim Hours</span>
                    <span className="text-gray-300">{config.time_config.total_simulation_hours}h</span>
                  </div>
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-gray-500">Min/Round</span>
                    <span className="text-gray-300">{config.time_config.minutes_per_round}m</span>
                  </div>
                </div>
              )}

              <button
                onClick={startSimulation}
                disabled={starting || !simulationId}
                className="w-full py-2.5 bg-green-500/20 hover:bg-green-500/30 border border-green-500/30 rounded text-green-400 text-sm font-mono transition-all disabled:opacity-50"
              >
                {starting ? 'Starting...' : '\u25b6 Launch Simulation'}
              </button>
            </div>
          </div>

          {/* Agent Profiles */}
          <div className="lg:col-span-2 bg-[#111118] border border-gray-800 rounded-lg overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-800 flex items-center gap-4">
              <button
                onClick={() => setActiveTab('twitter')}
                className={`text-xs font-mono px-3 py-1 rounded transition-all ${
                  activeTab === 'twitter' ? 'bg-blue-500/20 text-blue-400' : 'text-gray-500 hover:text-gray-300'
                }`}
              >
                Twitter ({profiles.twitter.length})
              </button>
              <button
                onClick={() => setActiveTab('reddit')}
                className={`text-xs font-mono px-3 py-1 rounded transition-all ${
                  activeTab === 'reddit' ? 'bg-orange-500/20 text-orange-400' : 'text-gray-500 hover:text-gray-300'
                }`}
              >
                Reddit ({profiles.reddit.length})
              </button>
            </div>
            <div className="p-4 max-h-96 overflow-y-auto">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {(activeTab === 'twitter' ? profiles.twitter : profiles.reddit).map(profile => (
                  <div key={profile.agent_id} className="p-3 bg-gray-900/50 rounded border border-gray-800">
                    <div className="flex items-center gap-2 mb-1">
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                        activeTab === 'twitter' ? 'bg-blue-500/20 text-blue-400' : 'bg-orange-500/20 text-orange-400'
                      }`}>
                        {profile.username[0]?.toUpperCase()}
                      </div>
                      <span className="text-sm font-mono text-gray-200">
                        {activeTab === 'twitter' ? '@' : 'u/'}{profile.username}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500">{profile.bio}</p>
                  </div>
                ))}
                {(activeTab === 'twitter' ? profiles.twitter : profiles.reddit).length === 0 && (
                  <div className="col-span-2 text-center text-gray-600 text-sm font-mono py-8">
                    No agents configured for this platform
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default OntologySimulation
