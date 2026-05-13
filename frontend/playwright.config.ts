import { defineConfig, devices } from '@playwright/test';

const frontendPort = 5176;
const backendPort = 8001;

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  workers: 1,
  reporter: [['list']],
  use: {
    baseURL: `http://127.0.0.1:${frontendPort}`,
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      command: `uv run --project backend python -m uvicorn backend.app.main:app --host 127.0.0.1 --port ${backendPort}`,
      cwd: '..',
      url: `http://127.0.0.1:${backendPort}/status`,
      reuseExistingServer: true,
      timeout: 30_000,
    },
    {
      command: `pnpm exec vite dev --host 127.0.0.1 --port ${frontendPort}`,
      url: `http://127.0.0.1:${frontendPort}/`,
      reuseExistingServer: true,
      timeout: 30_000,
      env: {
        PUBLIC_SAUTIRELAY_API_URL: `http://127.0.0.1:${backendPort}`,
      },
    },
  ],
});
