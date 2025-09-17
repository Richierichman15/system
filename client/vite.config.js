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
    // Use esbuild for faster builds
    minify: 'esbuild',
  },
  // Handle rollup issues in CI
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom', 'axios'],
  },
  // Use esbuild for faster builds and to avoid rollup issues
  esbuild: {
    target: 'es2020',
  },
})
