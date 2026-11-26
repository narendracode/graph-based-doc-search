import type { NextConfig } from "next";

// Next.js's dev server blocks cross-origin requests to /_next/* dev-only
// resources (the HMR websocket, and — critically — the JS/CSS chunks needed to
// actually render the page) unless the origin making the request is explicitly
// allowed. That matters here because the app gets accessed via a public
// IP/host (EC2), not just localhost — without this, the page loads an empty
// shell and nothing ever hydrates. Derived from WEB_ORIGIN (set by
// scripts/ec2-setup.sh to the deployment's actual public IP) so this stays in
// sync automatically instead of hardcoding an IP that can change.
function allowedDevOrigins(): string[] {
  const origins = new Set(["localhost", "127.0.0.1"]);
  const webOrigin = process.env.WEB_ORIGIN;
  if (webOrigin) {
    try {
      origins.add(new URL(webOrigin).hostname);
    } catch {
      // WEB_ORIGIN isn't a valid URL — ignore, local dev origins still apply.
    }
  }
  return [...origins];
}

const nextConfig: NextConfig = {
  allowedDevOrigins: allowedDevOrigins(),
};

export default nextConfig;
