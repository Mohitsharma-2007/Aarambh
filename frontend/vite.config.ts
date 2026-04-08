import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tsconfigPaths from 'vite-tsconfig-paths'
import path from 'path'

export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      // Stub experimental Three.js modules that three-globe imports
      'three/webgpu': path.resolve(__dirname, './src/stubs/three-webgpu.ts'),
      'three/tsl': path.resolve(__dirname, './src/stubs/three-tsl.ts'),
    },
  },
  server: {
    port: 5173,
    host: true,
    hmr: {
      port: 5173,
      host: 'localhost',
    },
    proxy: {
      // Proxy all /api requests to the FastAPI backend on port 8000
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
      // Proxy health check
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
