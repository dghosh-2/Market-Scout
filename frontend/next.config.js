/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // In production (Vercel), API routes are handled by the Python serverless function
    // In development, proxy to local FastAPI server
    const isDev = process.env.NODE_ENV === 'development'
    
    if (isDev) {
      return [
        {
          source: '/api/:path*',
          destination: 'http://localhost:8000/api/:path*',
        },
      ]
    }
    
    return []
  },
}

module.exports = nextConfig

