import { lazy, Suspense } from 'react'

// Lazy load essential pages only
export const NewsFeed = lazy(() => import('./NewsFeed'))
export const Economy = lazy(() => import('./Economy'))
export const Finance = lazy(() => import('./FinancePage'))
export const AIQuery = lazy(() => import('./AIQuery'))
export const GlobeView = lazy(() => import('./GlobeView'))

// Loading fallback
export function PageLoader() {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="flex flex-col items-center gap-3">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
        <span className="text-text-muted text-sm font-data">Loading module...</span>
      </div>
    </div>
  )
}

// Wrapper for lazy pages
export function LazyPage({ children }: { children: React.ReactNode }) {
  return (
    <Suspense fallback={<PageLoader />}>
      {children}
    </Suspense>
  )
}
