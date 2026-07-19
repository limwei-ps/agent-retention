import { defineConfig, devices } from "@playwright/test";

// Streaming E2E. Two webServers: the FastAPI backend in mock mode (deterministic, grounded, with a
// small per-token delay so the stream is observably incremental) and Next dev wired to it via the BFF.
// Relative cwd resolves against this config's directory (apps/web) → the sibling apps/api.
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  timeout: 60_000,
  expect: { timeout: 15_000 },
  reporter: process.env.CI ? "line" : [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
    permissions: ["clipboard-read", "clipboard-write"],
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: "uv run uvicorn app.main:app --port 8000",
      cwd: "../api",
      url: "http://localhost:8000/api/health",
      timeout: 120_000,
      reuseExistingServer: !process.env.CI,
      env: {
        LLM_MODE: "mock",
        SSE_TOKEN_CHUNK_DELAY_MS: "60",
        DATABASE_URL: "sqlite:///./e2e.db",
      },
    },
    {
      command: "pnpm exec next dev -p 3000",
      url: "http://localhost:3000",
      timeout: 120_000,
      reuseExistingServer: !process.env.CI,
      env: { API_BASE_URL: "http://localhost:8000" },
    },
  ],
});
