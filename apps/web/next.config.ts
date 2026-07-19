import path from "node:path";

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactCompiler: true,
  // Transpile the workspace TS package (contract types generated from the API OpenAPI schema).
  transpilePackages: ["@retention/shared-types"],
  // Self-contained server for Docker/Cloud Run: bundles a minimal node_modules + server.js (honors
  // $PORT), so the runtime image needs no pnpm/workspace. Trace from the monorepo root so the
  // workspace package is included.
  output: "standalone",
  outputFileTracingRoot: path.join(__dirname, "../../"),
};

export default nextConfig;
