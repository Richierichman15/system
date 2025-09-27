import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 6000,
    host: true,
  },
  build: {
    // Use esbuild for all builds to avoid rollup issues
    minify: 'esbuild',
    // Increase chunk size warning limit
    chunkSizeWarningLimit: 1000,
    // Disable rollup and use esbuild
    rollupOptions: undefined,
  },
  // Handle dependencies
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom', 'axios'],
  },
  // Use esbuild for faster builds and to avoid rollup issues
  esbuild: {
    target: 'es2020',
  },
})
