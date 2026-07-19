import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactCompiler: true,
  // Transpile the workspace TS package (contract types generated from the API OpenAPI schema).
  transpilePackages: ["@retention/shared-types"],
};

export default nextConfig;
