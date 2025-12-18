/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  modularizeImports: {
    "@mui/icons-material": {
      transform: "@mui/icons-material/{{member}}",
    },
  },
  // Rewrite or proxy to backend if needed in dev
  async rewrites() {
    return [
      {
        source: "/api/backend/:path*",
        destination: "http://localhost:8001/api/v1/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
