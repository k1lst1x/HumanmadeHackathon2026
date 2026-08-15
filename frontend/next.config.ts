import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactCompiler: true,
  // pin the workspace root so Next doesn't walk up into the home directory
  turbopack: { root: import.meta.dirname },
};

export default nextConfig;
