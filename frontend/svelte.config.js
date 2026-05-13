import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter({
      pages: 'build',
      assets: 'build',
      fallback: '200.html',
    }),
    prerender: {
      handleHttpError: ({ path, referrer, status }) => {
        if (status === 404 && referrer?.startsWith('/docs/')) {
          return;
        }

        throw new Error(`${status} ${path}${referrer ? ` linked from ${referrer}` : ''}`);
      },
    },
  },
};

export default config;
