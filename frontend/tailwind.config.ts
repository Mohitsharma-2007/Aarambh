import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Canvas
        'bg-primary': 'var(--bg-primary)',
        'bg-secondary': 'var(--bg-secondary)',
        'bg-tertiary': 'var(--bg-tertiary)',
        'bg-hover': 'var(--bg-hover)',
        'bg-active': 'var(--bg-active)',
        // Text
        'text-primary': 'var(--text-primary)',
        'text-secondary': 'var(--text-secondary)',
        'text-muted': 'var(--text-muted)',
        // Domain Colors
        'geo': 'var(--geo)',
        'eco': 'var(--eco)',
        'def': 'var(--def)',
        'tech': 'var(--tech)',
        'cli': 'var(--cli)',
        'soc': 'var(--soc)',
        // Status
        'online': 'var(--online)',
        'warning': 'var(--warning)',
        'error': 'var(--error)',
        'idle': 'var(--idle)',
        // Accents
        'accent': 'var(--accent)',
        'accent-2': 'var(--accent-2)',
      },
      fontFamily: {
        'ui': ['Geist', '-apple-system', 'sans-serif'],
        'data': ['IBM Plex Mono', 'Geist Mono', 'monospace'],
        'cmd': ['IBM Plex Mono', 'monospace'],
      },
      fontSize: {
        'xs': '11px',
        'sm': '12px',
        'base': '13px',
        'md': '14px',
        'lg': '16px',
        'xl': '20px',
        '2xl': '24px',
        '3xl': '30px',
      },
      animation: {
        'pulse-blue': 'pulse-blue 2s infinite',
        'pulse-green': 'pulse-green 2s infinite',
        'pulse-red': 'pulse-red 2s infinite',
        'pulse-amber': 'pulse-amber 2s infinite',
        'scan': 'scan 8s linear infinite',
        'slide-in': 'slide-in 0.3s ease forwards',
      },
      keyframes: {
        'pulse-blue': {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(74,158,237,.7)' },
          '50%': { boxShadow: '0 0 0 6px rgba(74,158,237,0)' },
        },
        'pulse-green': {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(34,197,94,.7)' },
          '50%': { boxShadow: '0 0 0 6px rgba(34,197,94,0)' },
        },
        'pulse-red': {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(239,68,68,.7)' },
          '50%': { boxShadow: '0 0 0 6px rgba(239,68,68,0)' },
        },
        'pulse-amber': {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(245,158,11,.7)' },
          '50%': { boxShadow: '0 0 0 6px rgba(245,158,11,0)' },
        },
        'scan': {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
        'slide-in': {
          'from': { opacity: '0', transform: 'translateX(20px)' },
          'to': { opacity: '1', transform: 'translateX(0)' },
        },
      },
    },
  },
  plugins: [],
}

export default config
