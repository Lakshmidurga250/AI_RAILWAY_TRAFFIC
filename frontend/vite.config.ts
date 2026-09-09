import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/auth': 'http://localhost:8000',
      '/trains': 'http://localhost:8000',
      '/stations': 'http://localhost:8000',
      '/network': 'http://localhost:8000',
      '/simulation': 'http://localhost:8000',
      '/ai': 'http://localhost:8000',
      '/optimization': 'http://localhost:8000',
      '/conflicts': 'http://localhost:8000',
      '/analytics': 'http://localhost:8000',
      '/reports': 'http://localhost:8000',
      '/models': 'http://localhost:8000',
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true
      }
    }
  }
});
