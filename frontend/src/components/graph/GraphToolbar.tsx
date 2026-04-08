import { RefreshCw, ZoomIn, ZoomOut, Layers, Grid3X3, Circle, Filter } from 'lucide-react'
import { useGraphStore } from '@/store/graph.store'
import { cn } from '@/utils/cn'

export default function GraphToolbar() {
  const { layout, setLayout, viewMode, setViewMode, isLoading } = useGraphStore()

  return (
    <div className="flex items-center gap-1 px-3 py-2 bg-bg-secondary border-b border-border-subtle">
      {/* Layout buttons */}
      <div className="flex items-center gap-1 mr-4">
        <button
          onClick={() => setLayout('force')}
          className={cn(
            'toolbar-btn',
            layout === 'force' && 'toolbar-btn--active'
          )}
          title="Force layout"
        >
          <Circle className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={() => setLayout('hierarchical')}
          className={cn(
            'toolbar-btn',
            layout === 'hierarchical' && 'toolbar-btn--active'
          )}
          title="Hierarchical layout"
        >
          <Layers className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={() => setLayout('circular')}
          className={cn(
            'toolbar-btn',
            layout === 'circular' && 'toolbar-btn--active'
          )}
          title="Circular layout"
        >
          <Grid3X3 className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="w-px h-4 bg-border-subtle" />

      {/* View mode */}
      <div className="flex items-center gap-1 ml-4 mr-4">
        <button
          onClick={() => setViewMode('2d')}
          className={cn(
            'toolbar-btn',
            viewMode === '2d' && 'toolbar-btn--active'
          )}
        >
          2D
        </button>
        <button
          onClick={() => setViewMode('3d')}
          className={cn(
            'toolbar-btn',
            viewMode === '3d' && 'toolbar-btn--active'
          )}
        >
          3D
        </button>
      </div>

      <div className="w-px h-4 bg-border-subtle" />

      {/* Actions */}
      <div className="flex items-center gap-1 ml-4">
        <button className="toolbar-btn" title="Refresh graph">
          <RefreshCw className={cn('w-3.5 h-3.5', isLoading && 'animate-spin')} />
        </button>
        <button className="toolbar-btn" title="Zoom in">
          <ZoomIn className="w-3.5 h-3.5" />
        </button>
        <button className="toolbar-btn" title="Zoom out">
          <ZoomOut className="w-3.5 h-3.5" />
        </button>
        <button className="toolbar-btn" title="Filter nodes">
          <Filter className="w-3.5 h-3.5" />
        </button>
      </div>

      <style>{`
        .toolbar-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 28px;
          height: 24px;
          border-radius: 4px;
          font-size: 11px;
          color: var(--text-muted);
          background: transparent;
          border: 1px solid transparent;
          transition: all 0.1s ease;
        }
        .toolbar-btn:hover {
          background: var(--bg-hover);
          color: var(--text-primary);
        }
        .toolbar-btn--active {
          background: var(--bg-active);
          color: var(--accent);
          border-color: var(--border-focus);
        }
      `}</style>
    </div>
  )
}
