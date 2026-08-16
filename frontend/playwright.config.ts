import { defineConfig, devices } from "@playwright/test";

// First e2e test in this repo -- establishes the convention (see
// SPRINT_JULES_MEGA_AUTOMATION_E2E_TESTS.md-style rationale: exercise the
// real stack, not a mocked one). Both the real backend (uvicorn, a
// throwaway SQLite DB so this never touches dev/trial data) and the real
// frontend dev server are started automatically for local runs and CI
// alike -- nothing to remember to start by hand.
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "list",
  use: {
    baseURL: "http://localhost:5173",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command: "python -m uvicorn api.main:app --host 0.0.0.0 --port 8000",
      cwd: "..",
      url: "http://localhost:8000/health",
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
      env: {
        API_ENV: "development",
        JWT_SECRET: "e2e-test-secret-not-for-production-use-32b",
        DATABASE_URL: "sqlite:///e2e_test.db",
      },
    },
    {
      command: "npm run dev -- --port 5173",
      url: "http://localhost:5173",
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
      env: {
        VITE_API_URL: "http://localhost:8000",
        VITE_WS_URL: "ws://localhost:8000",
      },
    },
  ],
});
