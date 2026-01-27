import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable React strict mode for better development experience
  reactStrictMode: true,

  // Production optimizations
  compress: true,

  // Optimize images
  images: {
    formats: ["image/avif", "image/webp"],
  },

  // Experimental features for better performance
  experimental: {
    // Optimize package imports for better tree-shaking
    optimizePackageImports: ["recharts", "lucide-react"],
  },

  // Turbopack configuration (Next.js 16+ default bundler)
  turbopack: {
    // Empty config to acknowledge Turbopack usage
    // Turbopack handles optimizations automatically
  },

  // Performance headers
  headers: async () => [
    {
      source: "/:all*(svg|jpg|png|webp|avif)",
      headers: [
        {
          key: "Cache-Control",
          value: "public, max-age=31536000, immutable",
        },
      ],
    },
    {
      source: "/_next/static/:path*",
      headers: [
        {
          key: "Cache-Control",
          value: "public, max-age=31536000, immutable",
        },
      ],
    },
  ],
};

export default nextConfig;
