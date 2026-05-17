// Strangler-fig routing — {{DOMAIN}}
// Cloudflare Worker. Deploy with: wrangler deploy
//
// Environment variables (set via wrangler.toml or dashboard):
//   LEGACY_BASE     e.g. https://legacy.example.com
//   NEW_BASE        e.g. https://new.example.com
//   RAMP_PERCENT    integer 0..100
//   KILL_SWITCH     "true" forces all traffic to legacy
//   DOMAIN_NAME     e.g. "auth"

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Only route paths owned by this domain
    if (!url.pathname.startsWith(`/api/${env.DOMAIN_NAME}/`)) {
      return new Response("Not in scope", { status: 404 });
    }

    // Kill switch: instant rollback
    if (env.KILL_SWITCH === "true") {
      return forward(request, env.LEGACY_BASE, "legacy", "kill-switch");
    }

    // Header override (used by canary cohorts / synthetic probes)
    const cohort = request.headers.get("X-Migration-Cohort");
    if (cohort === "new") return forward(request, env.NEW_BASE, "new", "cohort");
    if (cohort === "legacy") return forward(request, env.LEGACY_BASE, "legacy", "cohort");

    // Sticky bucketing by user_id (from JWT or cookie)
    const userId = await extractUserId(request);
    const bucket = userId ? djb2Hash(userId) % 100 : Math.floor(Math.random() * 100);
    const ramp = parseInt(env.RAMP_PERCENT || "0", 10);

    if (bucket < ramp) {
      return forward(request, env.NEW_BASE, "new", "ramp");
    } else {
      return forward(request, env.LEGACY_BASE, "legacy", "ramp");
    }
  },
};

async function forward(request, base, label, reason) {
  const url = new URL(request.url);
  const target = base + url.pathname + url.search;
  const upstream = new Request(target, request);
  upstream.headers.set("X-Migration-Route", label);
  upstream.headers.set("X-Migration-Reason", reason);

  const start = Date.now();
  let response;
  try {
    response = await fetch(upstream);
  } catch (e) {
    return new Response(`upstream error: ${e.message}`, { status: 502 });
  }
  const elapsed = Date.now() - start;

  // Echo routing decision on the response for observability
  const out = new Response(response.body, response);
  out.headers.set("X-Migration-Route", label);
  out.headers.set("X-Migration-Latency-Ms", String(elapsed));
  return out;
}

function djb2Hash(s) {
  let h = 5381;
  for (let i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) | 0;
  return Math.abs(h);
}

async function extractUserId(request) {
  // 1. JWT in Authorization header
  const auth = request.headers.get("Authorization");
  if (auth && auth.startsWith("Bearer ")) {
    try {
      const payload = JSON.parse(atob(auth.slice(7).split(".")[1]));
      if (payload.sub) return payload.sub;
    } catch (_) {}
  }
  // 2. Cookie
  const cookie = request.headers.get("Cookie") || "";
  const m = cookie.match(/(?:^|;\s*)user_id=([^;]+)/);
  if (m) return decodeURIComponent(m[1]);
  return null;
}
