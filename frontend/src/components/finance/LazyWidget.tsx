import { useState, useEffect, useRef, memo } from 'react';

interface LazyWidgetProps {
  children: React.ReactNode;
  height?: string;
  placeholder?: string;
}

/**
 * LazyWidget - Only renders its children when the container enters the viewport.
 * Uses IntersectionObserver for performant scroll-triggered loading.
 */
const LazyWidget: React.FC<LazyWidgetProps> = ({ children, height = '500px', placeholder = 'Loading widget...' }) => {
  const [isVisible, setIsVisible] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: '200px' } // Preload 200px before in view
    );

    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={ref} style={{ minHeight: height }}>
      {isVisible ? (
        children
      ) : (
        <div className="flex items-center justify-center bg-[#0D0F14] border border-white/5 rounded-2xl animate-pulse" style={{ height }}>
          <span className="text-xs text-white/20 font-mono uppercase tracking-widest">{placeholder}</span>
        </div>
      )}
    </div>
  );
};

export default memo(LazyWidget);
