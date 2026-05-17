# Sub-Agent: UI Screen Crawl

You produce a Playwright crawler that enumerates UI states of the running legacy app and screenshot every screen. Each unique screen represents at least one feature.

---

## Parameters

- `{{LEGACY_URL}}` — URL of running legacy app (e.g., `http://localhost:3000`)
- `{{TEST_USER_EMAIL}}` / `{{TEST_USER_PASSWORD}}` — credentials for an account with broad access
- `{{ROUTES_FILE}}` (optional) — path to a JSON file listing known routes; if absent, this agent auto-discovers from API routes scan output

---

## Output Files

- `discovery/screens/manifest.json` — list of routes + screenshot paths + observed elements
- `discovery/screens/*.png` — one screenshot per route, per state
- `discovery/screens/crawler.js` — the crawler script (so it can be re-run)

---

## Context Budget

Do not load screenshots into your context. Reference only the manifest.

---

## Step 1 — Build the route list

If `{{ROUTES_FILE}}` is provided, use it. Otherwise derive from `discovery/modules/*/api-routes.md` plus a heuristic list:

```
/login, /register, /forgot-password
/dashboard, /home, /
/settings, /profile, /account
/admin, /admin/users, /admin/audit
{per-resource: /{resource}, /{resource}/new, /{resource}/:id, /{resource}/:id/edit}
```

For each resource discovered in `discovery/schemas/`, generate CRUD routes.

---

## Step 2 — Write `discovery/screens/crawler.js`

```javascript
// discovery/screens/crawler.js
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE = process.env.LEGACY_URL || '{{LEGACY_URL}}';
const EMAIL = process.env.TEST_USER_EMAIL || '{{TEST_USER_EMAIL}}';
const PASSWORD = process.env.TEST_USER_PASSWORD || '{{TEST_USER_PASSWORD}}';
const OUT_DIR = path.resolve(__dirname);

const routes = JSON.parse(fs.readFileSync(path.join(OUT_DIR, 'routes.json'), 'utf-8'));

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const manifest = { base: BASE, captured_at: new Date().toISOString(), routes: [] };

  // 1. anonymous capture
  for (const r of routes.anonymous || []) {
    await page.goto(`${BASE}${r}`, { waitUntil: 'networkidle' }).catch(() => {});
    const file = `anon${r.replace(/[\/:?&=]/g, '-')}.png`;
    await page.screenshot({ path: path.join(OUT_DIR, file), fullPage: true });
    manifest.routes.push({ auth: 'anon', route: r, file });
  }

  // 2. sign in
  await page.goto(`${BASE}/login`);
  await page.fill('input[type=email], input[name=email], input[name=username]', EMAIL);
  await page.fill('input[type=password], input[name=password]', PASSWORD);
  await page.click('button[type=submit]');
  await page.waitForLoadState('networkidle');

  // 3. authenticated capture
  for (const r of routes.authenticated || []) {
    try {
      await page.goto(`${BASE}${r}`, { waitUntil: 'networkidle' });
      const file = `auth${r.replace(/[\/:?&=]/g, '-')}.png`;
      await page.screenshot({ path: path.join(OUT_DIR, file), fullPage: true });
      const title = await page.title();
      manifest.routes.push({ auth: 'user', route: r, file, title });
    } catch (e) {
      manifest.routes.push({ auth: 'user', route: r, error: e.message });
    }
  }

  fs.writeFileSync(path.join(OUT_DIR, 'manifest.json'), JSON.stringify(manifest, null, 2));
  await browser.close();
})();
```

---

## Step 3 — Write `discovery/screens/routes.json`

```json
{
  "anonymous": ["/login", "/register", "/forgot-password", "/"],
  "authenticated": [
    "/dashboard",
    "/settings",
    "/profile",
    "/admin",
    "/{resource}",
    "/{resource}/new"
  ]
}
```

Replace `{resource}` placeholders with actual resources from `discovery/schemas/`.

---

## Step 4 — Instructions for the human

Print instructions to run the crawler:

```bash
cd discovery/screens
npm init -y && npm i playwright
npx playwright install chromium
LEGACY_URL={{LEGACY_URL}} TEST_USER_EMAIL={{TEST_USER_EMAIL}} TEST_USER_PASSWORD={{TEST_USER_PASSWORD}} node crawler.js
```

Do NOT run the crawler from this agent (you do not have a browser). Surface to the user.

---

## Completion

```
[UI-SCREEN-CRAWL SCAFFOLDED]
Crawler: discovery/screens/crawler.js
Routes: discovery/screens/routes.json
Run with: (instructions above)
Once complete, discovery/screens/manifest.json will list all captured screens.
```
