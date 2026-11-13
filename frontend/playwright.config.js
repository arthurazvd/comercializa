import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false, // Sequencial para manter consistência do banco SQLite nos testes de sistema
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['json', { outputFile: 'test-results/p3-report.json' }],
    ['list']
  ],
  use: {
    baseURL: 'http://127.0.0.1:4173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'Desktop Chrome',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'Mobile Safari (Usabilidade)',
      use: { ...devices['iPhone 13'] },
      testMatch: /usability-a11y\.spec\.js/,
    },
  ],
  webServer: [
    {
      command: 'cd ../backend && if [ -f .venv/bin/python ]; then .venv/bin/python manage.py migrate && .venv/bin/python manage.py runserver 127.0.0.1:8000; elif command -v python3 >/dev/null 2>&1; then python3 manage.py migrate && python3 manage.py runserver 127.0.0.1:8000; else python manage.py migrate && python manage.py runserver 127.0.0.1:8000; fi',
      url: 'http://127.0.0.1:8000/api/health/',
      reuseExistingServer: !process.env.CI,
      timeout: 120 * 1000,
    },
    {
      command: 'npm run build && npm run preview -- --host 127.0.0.1 --port 4173',
      url: 'http://127.0.0.1:4173',
      reuseExistingServer: !process.env.CI,
      timeout: 120 * 1000,
    },
  ],
});