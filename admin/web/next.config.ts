import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  basePath: "/fridge2fork",
  assetPrefix: "/fridge2fork",
  transpilePackages: ["@mui/material", "@mui/icons-material"],
  experimental: {
    optimizePackageImports: ["@mui/material", "@mui/icons-material"],
  },
};

export default nextConfig;
