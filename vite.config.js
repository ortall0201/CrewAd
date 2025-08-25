import { defineConfig } from 'vite';

export default defineConfig({
  root: './folder-in-ad-out/frontend',
  server: {
    host: true,
    port: 5173,
    strictPort: true
  }
});
