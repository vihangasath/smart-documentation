import type { NextConfig } from "next";

// NEXT_PUBLIC_* variables are inlined by Next.js automatically. In production
// a missing API URL would silently point the app at localhost, so fail loudly.
if (process.env.NODE_ENV === "production" && !process.env.NEXT_PUBLIC_API_URL) {
  throw new Error(
    "NEXT_PUBLIC_API_URL must be set for production builds (the URL of the Structify backend).",
  );
}

const nextConfig: NextConfig = {
  // Allow Next.js Image component to serve the local logo
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
