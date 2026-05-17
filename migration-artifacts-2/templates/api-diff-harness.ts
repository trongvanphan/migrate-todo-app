// API-Diff Harness — replay recorded traffic against legacy and new, emit diff JSONL.
//
// Usage:
//   LEGACY_BASE=https://legacy NEW_BASE=https://new \
//     npx ts-node harness.ts traffic.jsonl > harness-output.jsonl
//
// Input (one JSON object per line in traffic.jsonl):
//   { "method": "GET", "path": "/api/auth/me", "headers": {...}, "body": null }
//
// Output (one JSON object per line):
//   { "request": {...}, "legacy_response": {...}, "new_response": {...},
//     "outcome": "match|status-diff|body-diff|header-diff|error",
//     "diff_paths": ["$.amount"] }

import * as fs from "node:fs";
import * as readline from "node:readline";
import * as yaml from "yaml";

const LEGACY_BASE = required("LEGACY_BASE");
const NEW_BASE = required("NEW_BASE");
const EQUIV_PATH = process.env.EQUIVALENCE_YAML || "equivalence.yaml";

const equivalence: any = fs.existsSync(EQUIV_PATH)
  ? yaml.parse(fs.readFileSync(EQUIV_PATH, "utf-8"))
  : { defaults: {}, endpoints: [], expected_diffs: [], hard_fail: {} };

function required(name: string): string {
  const v = process.env[name];
  if (!v) {
    console.error(`Missing required env var: ${name}`);
    process.exit(2);
  }
  return v;
}

type Req = { method: string; path: string; headers?: Record<string, string>; body?: any };
type Resp = { status: number; headers: Record<string, string>; body: any };

async function callOne(base: string, req: Req): Promise<Resp> {
  const headers: Record<string, string> = { ...(req.headers || {}) };
  const init: RequestInit = { method: req.method, headers };
  if (req.body !== undefined && req.body !== null && !["GET", "HEAD"].includes(req.method)) {
    init.body = typeof req.body === "string" ? req.body : JSON.stringify(req.body);
    headers["Content-Type"] = headers["Content-Type"] || "application/json";
  }
  const res = await fetch(base + req.path, init);
  const text = await res.text();
  let body: any = text;
  try { body = JSON.parse(text); } catch (_) {}
  const respHeaders: Record<string, string> = {};
  res.headers.forEach((v, k) => (respHeaders[k] = v));
  return { status: res.status, headers: respHeaders, body };
}

function rulesFor(req: Req): any {
  const defaults = equivalence.defaults || {};
  const ep = (equivalence.endpoints || []).find(
    (e: any) => e.path === req.path && (!e.method || e.method === req.method)
  );
  return {
    ignore_response_headers: new Set([
      ...(defaults.ignore_response_headers || []),
      ...((ep && ep.overrides?.ignore_response_headers) || []),
    ].map((h: string) => h.toLowerCase())),
    ignore_body_paths: [
      ...(defaults.ignore_body_paths || []),
      ...((ep && ep.overrides?.ignore_body_paths) || []),
    ],
    array_order_independent:
      ep?.overrides?.array_order_independent ?? defaults.array_order_independent ?? false,
    number_precision: defaults.number_precision ?? 4,
    trim_strings: defaults.trim_strings ?? true,
  };
}

function stripPaths(obj: any, paths: string[]): any {
  // Very simple JSONPath-ish stripper supporting $.a.b, $.a[*].b, $.* etc.
  // For production, swap in a real jsonpath library.
  const clone = JSON.parse(JSON.stringify(obj));
  for (const p of paths) walk(clone, p.replace(/^\$\.?/, "").split("."), 0);
  return clone;

  function walk(node: any, parts: string[], i: number) {
    if (node == null || i >= parts.length) return;
    const part = parts[i];
    if (part === "*") {
      if (Array.isArray(node)) node.forEach((c) => walk(c, parts, i + 1));
      else if (typeof node === "object") Object.values(node).forEach((c) => walk(c, parts, i + 1));
    } else if (part.endsWith("[*]")) {
      const key = part.slice(0, -3);
      const arr = node[key];
      if (Array.isArray(arr)) arr.forEach((c) => walk(c, parts, i + 1));
    } else if (i === parts.length - 1) {
      if (Array.isArray(node)) node.forEach((c) => c && delete c[part]);
      else if (node && typeof node === "object") delete node[part];
    } else {
      walk(node[part], parts, i + 1);
    }
  }
}

function normalize(value: any, precision: number, trim: boolean): any {
  if (typeof value === "number") return Number(value.toFixed(precision));
  if (typeof value === "string") return trim ? value.trim() : value;
  if (Array.isArray(value)) return value.map((v) => normalize(v, precision, trim));
  if (value && typeof value === "object") {
    const out: any = {};
    for (const k of Object.keys(value).sort()) out[k] = normalize(value[k], precision, trim);
    return out;
  }
  return value;
}

function deepDiff(a: any, b: any, prefix = "$"): string[] {
  if (a === b) return [];
  if (typeof a !== typeof b) return [prefix];
  if (a == null || b == null) return [prefix];
  if (typeof a !== "object") return a === b ? [] : [prefix];
  const out: string[] = [];
  const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
  for (const k of keys) out.push(...deepDiff(a[k], b[k], `${prefix}.${k}`));
  return out;
}

function compare(req: Req, legacy: Resp, neu: Resp) {
  const rules = rulesFor(req);

  // Status class compare
  const statusClass = (s: number) => Math.floor(s / 100);
  if (statusClass(legacy.status) !== statusClass(neu.status)) {
    return { outcome: "status-diff", diff_paths: [`status:${legacy.status}!=${neu.status}`] };
  }

  // Header compare
  const headerDiffs: string[] = [];
  for (const h of Object.keys(legacy.headers)) {
    if (rules.ignore_response_headers.has(h.toLowerCase())) continue;
    if (legacy.headers[h] !== neu.headers[h]) headerDiffs.push(`header:${h}`);
  }
  if (headerDiffs.length > 0) {
    return { outcome: "header-diff", diff_paths: headerDiffs };
  }

  // Body compare
  const a = normalize(stripPaths(legacy.body, rules.ignore_body_paths), rules.number_precision, rules.trim_strings);
  const b = normalize(stripPaths(neu.body, rules.ignore_body_paths), rules.number_precision, rules.trim_strings);
  const diffs = deepDiff(a, b);
  if (diffs.length === 0) return { outcome: "match", diff_paths: [] };
  return { outcome: "body-diff", diff_paths: diffs.slice(0, 10) };
}

async function main() {
  const inputPath = process.argv[2];
  if (!inputPath) {
    console.error("Usage: harness.ts <traffic.jsonl>");
    process.exit(2);
  }
  const rl = readline.createInterface({ input: fs.createReadStream(inputPath) });
  let total = 0, matched = 0;

  for await (const line of rl) {
    if (!line.trim()) continue;
    total += 1;
    let req: Req;
    try { req = JSON.parse(line); } catch (e) { continue; }

    let legacy: Resp, neu: Resp, errored = false, errMsg = "";
    try {
      [legacy, neu] = await Promise.all([callOne(LEGACY_BASE, req), callOne(NEW_BASE, req)]);
    } catch (e: any) {
      errored = true;
      errMsg = e?.message || String(e);
      legacy = neu = { status: 0, headers: {}, body: null };
    }

    let result: any;
    if (errored) {
      result = { outcome: "error", diff_paths: [errMsg] };
    } else {
      result = compare(req, legacy, neu);
      if (result.outcome === "match") matched += 1;
    }

    process.stdout.write(JSON.stringify({
      request: req,
      legacy_response: { status: legacy.status, headers: legacy.headers, body: legacy.body },
      new_response: { status: neu.status, headers: neu.headers, body: neu.body },
      ...result,
    }) + "\n");
  }

  console.error(`harness: ${matched}/${total} matched (${((matched / total) * 100).toFixed(2)}%)`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
