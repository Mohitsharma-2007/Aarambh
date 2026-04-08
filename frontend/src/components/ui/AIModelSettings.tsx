import React from 'react'
import { Sparkles } from 'lucide-react'
import { useAIStore } from '@/store/ai.store'
import { cn } from '@/utils/cn'

interface AIModelSettingsProps {
    className?: string
    innerClassName?: string
    showDescription?: boolean
    description?: string
    layout?: 'vertical' | 'horizontal'
}

export const AIModelSettings: React.FC<AIModelSettingsProps> = ({
    className,
    innerClassName,
    showDescription = true,
    description = "Selection affects Knowledge Discovery, Temporal Simulation, and Strategic Intelligence generation.",
    layout = 'vertical'
}) => {
    const { providers, selectedProvider, selectedModel, setProvider, setModel } = useAIStore()

    const currentProvider = providers.find(p => p.id === selectedProvider)
    const availableModels = currentProvider?.models || []

    if (layout === 'horizontal') {
        return (
            <div className={cn("flex items-center gap-4", className)}>
                <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider whitespace-nowrap">
                        Provider
                    </span>
                    <select
                        value={selectedProvider}
                        onChange={(e) => setProvider(e.target.value)}
                        className="px-2 py-1 bg-bg-primary border border-border-subtle rounded text-[10px] text-text-primary focus:outline-none focus:border-accent min-w-[120px]"
                    >
                        {providers.map((p) => (
                            <option key={p.id} value={p.id} disabled={!p.available}>{p.name}</option>
                        ))}
                    </select>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider whitespace-nowrap">
                        Model
                    </span>
                    <select
                        value={selectedModel}
                        onChange={(e) => setModel(e.target.value)}
                        className="px-2 py-1 bg-bg-primary border border-border-subtle rounded text-[10px] text-text-primary font-mono focus:outline-none focus:border-accent min-w-[150px]"
                    >
                        {availableModels.map((m) => (
                            <option key={m.id} value={m.id}>{m.name}</option>
                        ))}
                    </select>
                </div>
            </div>
        )
    }

    return (
        <div className={cn("p-4 bg-bg-secondary border-b border-border-subtle", className)}>
            <div className={cn("max-w-2xl mx-auto grid grid-cols-2 gap-4", innerClassName)}>
                <div>
                    <label className="text-[10px] font-bold text-text-muted mb-2 block uppercase tracking-wider">
                        Intelligence Provider
                    </label>
                    <select
                        value={selectedProvider}
                        onChange={(e) => setProvider(e.target.value)}
                        className="w-full px-3 py-2 bg-bg-primary border border-border-subtle rounded text-xs text-text-primary focus:outline-none focus:border-accent transition-colors"
                    >
                        {providers.map((p) => (
                            <option key={p.id} value={p.id} disabled={!p.available}>{p.name}</option>
                        ))}
                    </select>
                </div>
                <div>
                    <label className="text-[10px] font-bold text-text-muted mb-2 block uppercase tracking-wider">
                        Analytical Model
                    </label>
                    <select
                        value={selectedModel}
                        onChange={(e) => setModel(e.target.value)}
                        className="w-full px-3 py-2 bg-bg-primary border border-border-subtle rounded text-xs text-text-primary font-mono focus:outline-none focus:border-accent transition-colors"
                    >
                        {availableModels.map((m) => (
                            <option key={m.id} value={m.id}>{m.name}</option>
                        ))}
                    </select>
                </div>
            </div>

            {showDescription && (
                <div className="mt-4 flex items-center justify-center gap-2 text-[10px] text-text-muted italic border-t border-border-subtle/30 pt-3">
                    <Sparkles className="w-3 h-3 text-accent" />
                    {description}
                </div>
            )}
        </div>
    )
}
