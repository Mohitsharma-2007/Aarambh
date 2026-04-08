import React, { lazy, Suspense } from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import App from './App'
import './styles/globals.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
})

// Lazy load pages
const LandingPage = lazy(() => import('./pages/LandingPage'))
const NewsFeed = lazy(() => import('./pages/NewsPage'))
const Economy = lazy(() => import('./pages/EconomyPage'))
const Finance = lazy(() => import('./pages/FinancePage'))
const GlobeView = lazy(() => import('./pages/GlobePage'))
const AIQuery = lazy(() => import('./pages/AIQuery'))


const PageLoader = () => (
  <div className="flex items-center justify-center h-screen">
    <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
  </div>
)

const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      // Landing
      { index: true, element: <Suspense fallback={<PageLoader />}><LandingPage /></Suspense> },
      // Core pages
      { path: 'news', element: <Suspense fallback={<PageLoader />}><NewsFeed /></Suspense> },
      { path: 'f2', element: <Suspense fallback={<PageLoader />}><NewsFeed /></Suspense> },
      { path: 'f10', element: <Suspense fallback={<PageLoader />}><Economy /></Suspense> },
      { path: 'finance', element: <Suspense fallback={<PageLoader />}><Finance /></Suspense> },
      { path: 'globe', element: <Suspense fallback={<PageLoader />}><GlobeView /></Suspense> },
      { path: 'query', element: <Suspense fallback={<PageLoader />}><AIQuery /></Suspense> },
    ],
  },
])

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </React.StrictMode>,
)
