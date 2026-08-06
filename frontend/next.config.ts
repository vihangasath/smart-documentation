import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Expose the backend API URL to the browser at build time
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },
  // Allow Next.js Image component to serve the local logo
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
