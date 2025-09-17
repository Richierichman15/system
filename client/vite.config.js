import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
  },
  build: {
    // Ensure consistent builds across environments
    rollupOptions: {
      external: [],
      output: {
        manualChunks: undefined,
      },
    },
    // Increase chunk size warning limit
    chunkSizeWarningLimit: 1000,
  },
  // Handle rollup issues in CI
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom', 'axios'],
  },
})
