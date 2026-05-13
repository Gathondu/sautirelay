import { paraglideVitePlugin } from '@inlang/paraglide-js';
import { defineConfig } from 'vite';
import { sveltekit } from '@sveltejs/kit/vite';

export default defineConfig({
  plugins: [
    sveltekit(),
    paraglideVitePlugin({
      project: './project.inlang',
      outdir: './src/lib/paraglide',
      emitTsDeclarations: true,
      strategy: ['localStorage', 'cookie', 'preferredLanguage', 'globalVariable', 'baseLocale'],
      urlPatterns: [],
    }),
  ],
  envPrefix: ['VITE_', 'PUBLIC_'],
  server: { fs: { allow: ['..'] } },
});
