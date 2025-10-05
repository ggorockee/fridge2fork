import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  basePath: "/fridge2fork",
  assetPrefix: "/fridge2fork",
  transpilePackages: ["@mui/material", "@mui/icons-material"],
  output: "standalone", // Enable standalone output for Docker
  eslint: {
    // Warning: This allows production builds to successfully complete even if
    // your project has ESLint errors.
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Warning: This allows production builds to successfully complete even if
    // your project has type errors.
    ignoreBuildErrors: true,
  },
  experimental: {
    optimizePackageImports: ["@mui/material", "@mui/icons-material"],
  },
};

export default nextConfig;
