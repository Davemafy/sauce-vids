/** @type {import('next').NextConfig} */
const basePath=process.env.NEXT_PUBLIC_SAUCE_BASE_PATH || undefined;
const nextConfig={reactStrictMode:true,...(basePath?{basePath}: {})};
export default nextConfig;
