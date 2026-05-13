import { defineConfig } from 'vite';
import { sveltekit } from '@sveltejs/kit/vite';

export default defineConfig({
  plugins: [sveltekit()],
  envPrefix: ['VITE_', 'PUBLIC_'],
  server: {
    fs: {
      allow: ['..'],
    },
  },
});
