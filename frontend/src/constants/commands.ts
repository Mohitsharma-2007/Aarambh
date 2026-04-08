export interface Command {
  name: string
  aliases: string[]
  description: string
  action: string
}

export const COMMANDS: Command[] = [
  {
    name: 'SEARCH',
    aliases: ['S', 'FIND', 'F'],
    description: 'Search for entities',
    action: 'search',
  },
  {
    name: 'ENTITY',
    aliases: ['E', 'OPEN', 'O'],
    description: 'Open entity profile',
    action: 'entity',
  },
  {
    name: 'GRAPH',
    aliases: ['G', 'NETWORK'],
    description: 'Open knowledge graph',
    action: 'graph',
  },
  {
    name: 'RESEARCH',
    aliases: ['R', 'DEEP'],
    description: 'Launch deep research',
    action: 'research',
  },
  {
    name: 'QUERY',
    aliases: ['Q', 'ASK', 'AI'],
    description: 'AI natural language query',
    action: 'query',
  },
  {
    name: 'ALERT',
    aliases: ['A', 'SIGNAL', 'MONITOR'],
    description: 'Create monitoring alert',
    action: 'alert',
  },
  {
    name: 'NEWS',
    aliases: ['N', 'FEED'],
    description: 'Filter news by domain',
    action: 'news',
  },
  {
    name: 'SIGNALS',
    aliases: ['ALERTS'],
    description: 'Open threat signal dashboard',
    action: 'signals',
  },
  {
    name: 'COMPARE',
    aliases: ['C', 'DIFF'],
    description: 'Side-by-side entity comparison',
    action: 'compare',
  },
  {
    name: 'TIMELINE',
    aliases: ['T', 'HISTORY'],
    description: 'Event timeline for entity',
    action: 'timeline',
  },
  {
    name: 'HELP',
    aliases: ['?', 'H'],
    description: 'Show all commands',
    action: 'help',
  },
  {
    name: 'CLEAR',
    aliases: ['CLS'],
    description: 'Clear current view',
    action: 'clear',
  },
]

export const parseCommand = (input: string): { command: Command | null; args: string } => {
  const parts = input.trim().split(/\s+/)
  const cmdStr = parts[0]?.toUpperCase() || ''
  const args = parts.slice(1).join(' ')

  const command = COMMANDS.find(
    (cmd) => cmd.name === cmdStr || cmd.aliases.includes(cmdStr)
  )

  return { command: command || null, args }
}

export const getCommandAction = (command: Command, args: string): string => {
  switch (command.action) {
    case 'search':
      return `/research?q=${encodeURIComponent(args)}`
    case 'entity':
      return `/research/${encodeURIComponent(args)}`
    case 'graph':
      return args ? `/graph?entity=${encodeURIComponent(args)}` : '/graph'
    case 'research':
      return `/deep-research?topic=${encodeURIComponent(args)}`
    case 'query':
      return `/query?q=${encodeURIComponent(args)}`
    case 'alert':
      return `/signals?action=create&keyword=${encodeURIComponent(args)}`
    case 'news':
      return `/news?domain=${encodeURIComponent(args.toLowerCase())}`
    case 'signals':
      return '/signals'
    case 'compare':
      const entities = args.split(/\s+vs\s+|\s+and\s+|\s+/)
      return `/research?compare=${entities.map(encodeURIComponent).join(',')}`
    case 'timeline':
      return `/research/${encodeURIComponent(args)}?tab=timeline`
    case 'help':
      return 'help'
    case 'clear':
      return 'clear'
    default:
      return '/'
  }
}
