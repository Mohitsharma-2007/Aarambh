export type Domain = 'geopolitics' | 'economics' | 'defense' | 'technology' | 'climate' | 'society'

export interface DomainConfig {
  label: string
  color: string
  bg: string
  icon: string
}

export const DOMAIN_CONFIG: Record<Domain, DomainConfig> = {
  geopolitics: {
    label: 'GEOPOLITICS',
    color: '#4a9eed',
    bg: 'rgba(74,158,237,0.12)',
    icon: 'Globe',
  },
  economics: {
    label: 'ECONOMICS',
    color: '#22c55e',
    bg: 'rgba(34,197,94,0.12)',
    icon: 'TrendingUp',
  },
  defense: {
    label: 'DEFENSE',
    color: '#ef4444',
    bg: 'rgba(239,68,68,0.12)',
    icon: 'Shield',
  },
  technology: {
    label: 'TECHNOLOGY',
    color: '#06b6d4',
    bg: 'rgba(6,182,212,0.12)',
    icon: 'Zap',
  },
  climate: {
    label: 'CLIMATE',
    color: '#14b8a6',
    bg: 'rgba(20,184,166,0.12)',
    icon: 'Leaf',
  },
  society: {
    label: 'SOCIETY',
    color: '#f59e0b',
    bg: 'rgba(245,158,11,0.12)',
    icon: 'Users',
  },
}

export const DOMAINS: Domain[] = [
  'geopolitics',
  'economics',
  'defense',
  'technology',
  'climate',
  'society',
]

export const getDomainConfig = (domain: Domain): DomainConfig => {
  return DOMAIN_CONFIG[domain]
}
