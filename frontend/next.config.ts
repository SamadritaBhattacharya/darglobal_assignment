import type { NextConfig } from "next";
import { PHASE_DEVELOPMENT_SERVER } from "next/constants";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

export default function config(phase: string): NextConfig {
  if (phase === PHASE_DEVELOPMENT_SERVER) {
    // `npm run dev`: forward /api/* to the FastAPI backend (rewrites don't work with static export)
    return {
      async rewrites() {
        return [{ source: "/api/:path*", destination: `${BACKEND_URL}/api/:path*` }];
      },
    };
  }
  return {
    output: "export", // static files, served by the FastAPI container
  };
}
