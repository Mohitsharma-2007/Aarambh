export interface Module {
  key: string
  label: string
  shortcut: string
  path: string
  description: string
}

export const MODULES: Module[] = [
  // Main F-Keys (Top Bar) - Matching PRD specifications
  {
    key: '1',
    label: 'Overview',
    shortcut: 'Alt+1',
    path: '/f1',
    description: 'Dashboard Overview',
  },
  {
    key: '2',
    label: 'News Feed',
    shortcut: 'Alt+2',
    path: '/f2',
    description: 'Live News and Updates',
  },
  {
    key: '3',
    label: 'Research',
    shortcut: 'Alt+3',
    path: '/f3',
    description: 'Research analysis',
  },
  {
    key: '4',
    label: 'Equity Research',
    shortcut: 'Alt+4',
    path: '/f4',
    description: 'Equity tools and research',
  },
  {
    key: '5',
    label: 'Ontology',
    shortcut: 'Alt+5',
    path: 'http://localhost:3000',
    description: 'Graph-based ontology simulation and prediction',
  },
  {
    key: '6',
    label: 'Investors',
    shortcut: 'Alt+6',
    path: '/f6',
    description: 'Investor tracking',
  },
  {
    key: '7',
    label: 'Signals',
    shortcut: 'Alt+7',
    path: '/f7',
    description: 'Event signals',
  },
  {
    key: '8',
    label: 'Charts',
    shortcut: 'Alt+8',
    path: '/f8',
    description: 'Interactive charts',
  },
  {
    key: '9',
    label: 'Quant',
    shortcut: 'Alt+9',
    path: '/f9',
    description: 'Quantitative analytics',
  },
  {
    key: '0',
    label: 'Sentiment',
    shortcut: 'Alt+0',
    path: '/f10',
    description: 'Macroeconomic indicators',
  },
  // Utilities (accessible via command palette or secondary menu)
  {
    key: 'O',
    label: 'Ontology',
    shortcut: 'Ctrl+O',
    path: 'http://localhost:3000',
    description: 'Graph-based ontology simulation and prediction',
  },
  {
    key: 'Q',
    label: 'AI Query',
    shortcut: 'Ctrl+Q',
    path: '/query',
    description: 'AI-powered query',
  },
  {
    key: 'D',
    label: 'Deep Research',
    shortcut: 'Ctrl+D',
    path: '/deep-research',
    description: 'Citations and deep research',
  },
  {
    key: 'I',
    label: 'Ingestion',
    shortcut: 'Ctrl+I',
    path: '/ingestion',
    description: 'Data ingestion pipelines',
  },
  {
    key: 'S',
    label: 'Settings',
    shortcut: 'Ctrl+S',
    path: '/settings',
    description: 'User preferences and system configuration',
  },
  {
    key: 'G',
    label: 'Globe View',
    shortcut: 'Ctrl+G',
    path: '/globe',
    description: 'Global geographic data',
  },
  {
    key: 'A',
    label: 'Analytics',
    shortcut: 'Ctrl+A',
    path: '/analytics',
    description: 'System and data analytics',
  },
  {
    key: 'K',
    label: 'Signals',
    shortcut: 'Ctrl+K',
    path: '/signals',
    description: 'Live alerts and signals',
  },
  {
    key: 'H',
    label: 'Dashboard',
    shortcut: 'Ctrl+H',
    path: '/dashboard',
    description: 'Home Dashboard',
  },
]

export const getModuleByPath = (path: string): Module | undefined => {
  return MODULES.find((m) => m.path === path)
}

export const getModuleByKey = (key: string): Module | undefined => {
  return MODULES.find((m) => m.key === key)
}