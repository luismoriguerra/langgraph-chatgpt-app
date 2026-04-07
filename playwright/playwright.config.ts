import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: "html",
  timeout: 30_000,

  use: {
    baseURL: "http://localhost:4321",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  webServer: [
    {
      command: "cd ../backend && ../.venv/bin/uvicorn app.main:app --port 8000",
      cwd: "..",
      url: "http://localhost:8000/docs",
      reuseExistingServer: true,
      timeout: 15_000,
    },
    {
      command: "cd ../frontend && npm run dev",
      cwd: "..",
      url: "http://localhost:4321",
      reuseExistingServer: true,
      timeout: 15_000,
    },
  ],
});
