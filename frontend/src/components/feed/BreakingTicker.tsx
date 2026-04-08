import { useState, useEffect, useRef } from 'react'

interface BreakingTickerProps {
  items: string[]
  speed?: number
}

export default function BreakingTicker({ items, speed = 50 }: BreakingTickerProps) {
  const [position, setPosition] = useState(0)
  const [contentWidth, setContentWidth] = useState(0)
  const containerRef = useRef<HTMLDivElement>(null)
  const contentRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (contentRef.current) {
      setContentWidth(contentRef.current.offsetWidth)
    }
  }, [items])

  useEffect(() => {
    const animate = () => {
      setPosition((prev) => {
        if (prev <= -contentWidth) {
          return 0
        }
        return prev - 1
      })
    }

    const interval = setInterval(animate, speed)
    return () => clearInterval(interval)
  }, [contentWidth, speed])

  if (items.length === 0) return null

  return (
    <div className="breaking-ticker">
      <div className="ticker-label">BREAKING</div>
      <div ref={containerRef} className="ticker-content-wrapper">
        <div
          ref={contentRef}
          className="ticker-content"
          style={{ transform: `translateX(${position}px)` }}
        >
          {items.map((item, i) => (
            <span key={i} className="ticker-item">
              {item}
            </span>
          ))}
          {/* Duplicate for seamless loop */}
          {items.map((item, i) => (
            <span key={`dup-${i}`} className="ticker-item">
              {item}
            </span>
          ))}
        </div>
      </div>

      <style>{`
        .breaking-ticker {
          display: flex;
          align-items: center;
          height: 28px;
          background: var(--bg-secondary);
          border-top: 1px solid var(--border-subtle);
          overflow: hidden;
        }
        .ticker-label {
          padding: 0 12px;
          font-family: 'IBM Plex Mono', monospace;
          font-size: 10px;
          font-weight: 700;
          color: var(--error);
          background: rgba(239,68,68,0.1);
          border-right: 1px solid var(--border-subtle);
          flex-shrink: 0;
        }
        .ticker-content-wrapper {
          flex: 1;
          overflow: hidden;
        }
        .ticker-content {
          display: flex;
          white-space: nowrap;
        }
        .ticker-item {
          padding: 0 24px;
          font-size: 12px;
          color: var(--text-secondary);
        }
        .ticker-item + .ticker-item::before {
          content: '•';
          margin-right: 24px;
          color: var(--accent);
        }
      `}</style>
    </div>
  )
}
