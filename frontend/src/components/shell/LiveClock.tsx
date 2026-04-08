import { useState, useEffect } from 'react'

export default function LiveClock() {
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  const timeStr = time.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  })

  const dateStr = time.toLocaleDateString('en-US', {
    weekday: 'short',
    day: '2-digit',
    month: 'short',
  })

  return (
    <div className="flex items-center gap-2 text-xs font-data text-text-muted">
      <span>{dateStr}</span>
      <span className="text-border-default">│</span>
      <span className="text-text-secondary">{timeStr}</span>
      <span className="text-accent text-[10px]">IST</span>
    </div>
  )
}
