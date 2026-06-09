import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Standalone output is required by the Phase 8 Docker image.
  output: "standalone",
};

export default nextConfig;
