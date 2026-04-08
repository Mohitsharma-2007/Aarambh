import { useState, useRef, useEffect } from 'react'
import { Loader2, AlertCircle, Database, Network, Activity, Settings, History, Sliders, Copy } from 'lucide-react'
import { cn } from '@/utils/cn'
import { api } from '@/api'
import { useAIStore } from '@/store/ai.store'
import { AIModelSettings } from '@/components/ui/AIModelSettings'

interface Entity {
    id: string
    name: string
    type: string
    importance: number
}

interface SimulationResult {
    scenario: string
    impact: string
    probability: number
    timeline: string
}

interface OntologyResearchResult {
    query: string
    entities: Entity[]
    relationships: Array<{ source: string; target: string; type: string }>
    research_data: Record<string, string>
    simulation_data: SimulationResult[]
    report: string
    tokens_used: number
}

export default function OntologyResearch() {
    const [query, setQuery] = useState('')
    const [rounds, setRounds] = useState(3)
    const [isRunning, setIsRunning] = useState(false)
    const [result, setResult] = useState<OntologyResearchResult | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [status, setStatus] = useState('')
    const { selectedProvider, selectedModel } = useAIStore()
    const [showProviderSettings, setShowProviderSettings] = useState(false)
    const [history, setHistory] = useState<any[]>([])
    const [showHistory, setShowHistory] = useState(false)
    const [historyLoading, setHistoryLoading] = useState(false)
    const resultRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        fetchHistory()
    }, [])

    async function fetchHistory() {
        setHistoryLoading(true)
        try {
            const data = await api.getResearchHistory(10)
            setHistory(data)
        } catch (err) {
            console.error('Failed to fetch history:', err)
        } finally {
            setHistoryLoading(false)
        }
    }

    async function runResearch() {
        if (!query.trim() || isRunning) return

        setIsRunning(true)
        setError(null)
        setResult(null)
        setStatus('Brainstorming entities...')

        try {
            const res = await api.runOntologyResearch({
                query: query.trim(),
                rounds: rounds,
                simulation: true,
                provider: selectedProvider,
                model: selectedModel
            })

            setResult(res as OntologyResearchResult)
            setStatus('Research complete')
            fetchHistory() // Refresh the history list

            // Scroll to result
            setTimeout(() => {
                resultRef.current?.scrollIntoView({ behavior: 'smooth' })
            }, 100)
        } catch (err: any) {
            console.error('Ontology research error:', err)
            setError(err?.response?.data?.detail || 'Research failed. Check backend connection.')
        } finally {
            setIsRunning(false)
        }
    }

    async function loadHistoryItem(id: string) {
        setIsRunning(true)
        setError(null)
        setStatus('Loading historical record...')
        try {
            const res = await api.getResearchDetail(id)
            // Transform research record back to expected research result format
            setResult({
                query: res.query,
                report: res.report,
                entities: res.entities,
                research_data: res.research_data,
                simulation_data: res.simulation_results?.simulation_data || [],
                tokens_used: 0,
                relationships: [] // Re-extraction from report would be needed for full graph
            } as any)
            setQuery(res.query)
            setShowHistory(false)
        } catch (err: any) {
            console.error('Failed to load history:', err)
            setError('Failed to load history item.')
        } finally {
            setIsRunning(false)
        }
    }

    function copyResult() {
        if (result?.report) {
            navigator.clipboard.writeText(result.report)
        }
    }

    return (
        <div className="h-full flex flex-col overflow-hidden">
            {/* Header with Settings */}
            <div className="flex items-center justify-between p-4 border-b border-border-subtle bg-bg-secondary">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-accent/20 flex items-center justify-center">
                        <Network className="w-4 h-4 text-accent" />
                    </div>
                    <div>
                        <h1 className="text-lg font-data font-semibold text-text-primary tracking-wide uppercase">
                            Ontology Engine
                        </h1>
                        <p className="text-[10px] text-text-muted">Autonomous Entity Research & Knowledge Mapping</p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setShowHistory(!showHistory)}
                        className={cn(
                            "p-2 rounded border transition-all",
                            showHistory ? "bg-accent text-bg-primary border-accent" : "bg-bg-primary border-border-subtle hover:border-border-default text-text-primary"
                        )}
                        title="View Research History"
                    >
                        <History className="w-4 h-4" />
                    </button>
                    <button
                        onClick={() => setShowProviderSettings(!showProviderSettings)}
                        className={cn(
                            "p-2 rounded border transition-all",
                            showProviderSettings ? "bg-accent text-bg-primary border-accent" : "bg-bg-primary border-border-subtle hover:border-border-default text-text-primary"
                        )}
                        title="AI Settings"
                    >
                        <Settings className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {/* History Panel */}
            {showHistory && (
                <div className="px-4 py-3 bg-bg-tertiary border-b border-border-subtle animate-in slide-in-from-top duration-200">
                    <div className="max-w-4xl mx-auto">
                        <div className="flex items-center justify-between mb-2">
                            <h3 className="text-[10px] font-data text-text-muted uppercase tracking-wider flex items-center gap-2">
                                <History className="w-3 h-3" /> Recent Research Records
                            </h3>
                            {historyLoading && <Loader2 className="w-3 h-3 animate-spin text-accent" />}
                        </div>
                        {history.length > 0 ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
                                {history.map((item) => (
                                    <button
                                        key={item.id}
                                        onClick={() => loadHistoryItem(item.id)}
                                        className="flex flex-col items-start p-2 bg-bg-primary border border-border-subtle rounded hover:border-accent transition-colors text-left group"
                                    >
                                        <span className="text-xs font-medium text-text-primary truncate w-full group-hover:text-accent transition-colors">
                                            {item.query}
                                        </span>
                                        <div className="flex items-center justify-between w-full mt-1">
                                            <span className="text-[8px] text-text-muted uppercase">
                                                {new Date(item.created_at).toLocaleDateString()}
                                            </span>
                                            {item.entities && (
                                                <span className="text-[7px] px-1 bg-bg-secondary rounded text-text-muted border border-border-subtle uppercase">
                                                    Saved
                                                </span>
                                            )}
                                        </div>
                                    </button>
                                ))}
                            </div>
                        ) : (
                            <div className="py-4 text-center border border-dashed border-border-subtle rounded-lg">
                                <p className="text-xs text-text-muted italic">No historical research records found.</p>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* AI Selection Header */}
            <div className="mx-4 mt-4 px-4 py-3 bg-bg-secondary/50 border border-border-subtle rounded-lg flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-accent/10 rounded-lg">
                        <Sliders className="w-4 h-4 text-accent" />
                    </div>
                    <div>
                        <div className="text-xs font-data font-semibold text-text-primary tracking-wider uppercase">
                            Intelligence Core
                        </div>
                        <div className="text-[10px] text-text-muted mt-0.5">
                            Select the model for deep strategic ontology research
                        </div>
                    </div>
                </div>
                <AIModelSettings showDescription={false} layout="horizontal" />
            </div>

            {/* Input Area */}
            <div className="p-4 bg-bg-secondary border-b border-border-subtle shadow-sm z-10">
                <div className="max-w-4xl mx-auto space-y-4">
                    <div className="flex items-end gap-4">
                        <div className="flex-1 space-y-1">
                            <label className="text-[10px] text-text-muted font-data uppercase">Strategic Query</label>
                            <textarea
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="Enter a complex query (e.g. 'Impact of Reliance expansion in green energy on Adani Group')"
                                className="w-full bg-bg-primary border border-border-subtle rounded p-2 text-sm text-text-primary focus:outline-none focus:border-accent resize-none"
                                rows={2}
                                disabled={isRunning}
                            />
                        </div>
                        <div className="w-24 space-y-1">
                            <label className="text-[10px] text-text-muted font-data uppercase">Rounds</label>
                            <input
                                type="number"
                                value={rounds}
                                onChange={(e) => setRounds(parseInt(e.target.value))}
                                min={1}
                                max={5}
                                className="w-full bg-bg-primary border border-border-subtle rounded p-2 text-sm text-center font-data"
                                disabled={isRunning}
                            />
                        </div>
                        <button
                            onClick={runResearch}
                            disabled={!query.trim() || isRunning}
                            className="px-6 py-2.5 bg-accent text-bg-primary rounded font-data text-xs hover:bg-accent/90 disabled:opacity-50 flex items-center gap-2"
                        >
                            {isRunning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Activity className="w-4 h-4" />}
                            {isRunning ? 'RESEARCHING...' : 'RUN ONTOLOGY'}
                        </button>
                    </div>
                    {isRunning && (
                        <div className="flex items-center gap-2 text-xs text-accent animate-pulse">
                            <div className="w-2 h-2 rounded-full bg-accent" />
                            {status}
                        </div>
                    )}
                </div>
            </div>

            {/* Results Area */}
            <div className="flex-1 overflow-y-auto p-4" ref={resultRef}>
                {error && (
                    <div className="max-w-4xl mx-auto bg-error/10 border border-error/30 rounded p-4 text-xs text-error mb-4 flex items-center gap-2">
                        <AlertCircle className="w-4 h-4" />
                        {error}
                    </div>
                )}

                {result ? (
                    <div className="max-w-4xl mx-auto space-y-6">
                        {/* Summary Stats */}
                        <div className="grid grid-cols-4 gap-4">
                            <div className="bg-bg-secondary border border-border-subtle rounded p-3 text-center">
                                <div className="text-[10px] text-text-muted font-data uppercase">Entities</div>
                                <div className="text-xl font-semibold text-text-primary">{result.entities.length}</div>
                            </div>
                            <div className="bg-bg-secondary border border-border-subtle rounded p-3 text-center">
                                <div className="text-[10px] text-text-muted font-data uppercase">Relationships</div>
                                <div className="text-xl font-semibold text-text-primary">{result.relationships.length}</div>
                            </div>
                            <div className="bg-bg-secondary border border-border-subtle rounded p-3 text-center">
                                <div className="text-[10px] text-text-muted font-data uppercase">Simulations</div>
                                <div className="text-xl font-semibold text-text-primary">{result.simulation_data?.length || 0}</div>
                            </div>
                            <div className="bg-bg-secondary border border-border-subtle rounded p-3 text-center">
                                <div className="text-[10px] text-text-muted font-data uppercase">Tokens</div>
                                <div className="text-xl font-semibold text-accent">{(result.tokens_used / 1000).toFixed(1)}k</div>
                            </div>
                        </div>

                        {/* Main Report */}
                        <div className="bg-bg-secondary border border-border-subtle rounded-lg overflow-hidden">
                            <div className="bg-bg-tertiary px-4 py-2 border-b border-border-subtle flex justify-between items-center">
                                <h3 className="text-[10px] font-data font-bold text-text-muted uppercase tracking-widest flex items-center gap-2">
                                    <Database className="w-3 h-3" />
                                    ELABORATED RESEARCH REPORT
                                </h3>
                                <button onClick={copyResult} className="text-text-muted hover:text-text-primary">
                                    <Copy className="w-3 h-3" />
                                </button>
                            </div>
                            <div className="p-6 prose prose-invert prose-sm max-w-none">
                                <div className="text-sm text-text-primary whitespace-pre-wrap leading-relaxed font-sans">
                                    {result.report}
                                </div>
                            </div>
                        </div>

                        {/* Simulations */}
                        {result.simulation_data && result.simulation_data.length > 0 && (
                            <div className="space-y-3">
                                <h3 className="text-[10px] font-data font-bold text-text-muted uppercase tracking-widest">
                                    STRATEGIC SIMULATIONS
                                </h3>
                                <div className="grid grid-cols-2 gap-4">
                                    {result.simulation_data.map((sim, i) => (
                                        <div key={i} className="bg-bg-secondary border border-border-subtle rounded p-4 space-y-2">
                                            <div className="flex justify-between items-start">
                                                <span className="text-xs font-bold text-accent">{sim.scenario}</span>
                                                <span className="text-[10px] font-data px-1.5 py-0.5 bg-bg-tertiary rounded">
                                                    {sim.probability}% PROB
                                                </span>
                                            </div>
                                            <p className="text-xs text-text-secondary leading-relaxed">{sim.impact}</p>
                                            <div className="text-[10px] text-text-muted italic">Timeline: {sim.timeline}</div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Knowledge Graph Snapshot */}
                        <div className="space-y-3">
                            <h3 className="text-[10px] font-data font-bold text-text-muted uppercase tracking-widest">
                                EXTRACTED ONTOLOGY (KG NODES)
                            </h3>
                            <div className="flex flex-wrap gap-2">
                                {result.entities.map((ent, i) => (
                                    <div key={i} className="bg-bg-secondary border border-border-subtle rounded px-2 py-1 flex items-center gap-2">
                                        <span className="text-xs text-text-primary font-medium">{ent.name}</span>
                                        <span className="text-[10px] text-text-muted uppercase font-data">{ent.type}</span>
                                        <div className="w-8 h-1 bg-bg-tertiary rounded-full overflow-hidden">
                                            <div className="h-full bg-accent" style={{ width: `${ent.importance}%` }} />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                ) : !isRunning && (
                    <div className="h-full flex flex-col items-center justify-center text-text-muted opacity-50 space-y-4">
                        <Network className="w-16 h-16" />
                        <div className="text-center">
                            <p className="text-sm font-medium">Ready for deep strategic research</p>
                            <p className="text-xs mt-1">Enter a query to begin building the autonomous ontology</p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
