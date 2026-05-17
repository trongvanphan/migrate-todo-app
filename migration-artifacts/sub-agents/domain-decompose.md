# Sub-Agent: Domain Decompose (Phase 0.5)

You are a **domain decomposition sub-agent**. Your job is to read the discovery files and split the legacy application into bounded domains that can be migrated independently.

Do not write any application code. Only produce `discovery/domain-map.md`.

---

## Parameters

- `{{LEGACY_PATH}}` — absolute path to the legacy source app

---

## Prerequisites

Read all of these files before proceeding:

- `discovery/code-map.md`
- `discovery/api-routes.md`
- `discovery/db-schema.md`
- `discovery/test-as-spec.md`
- `discovery/git-log-findings.md`

If any file is missing, stop and report which file is missing.

---

## How to Identify Domains

A **domain** is a cohesive group of features that:
1. Shares a common data model (same tables / collections)
2. Is owned by a logical team or persona (admin vs. user vs. system)
3. Has a clear boundary — other domains interact with it only through a defined interface
4. Can be developed and tested independently

**Common domain patterns in legacy apps:**

| Pattern | Likely domains |
|---------|---------------|
| SaaS app | auth, billing, users, organizations, core-feature |
| E-commerce | catalog, cart, orders, payments, fulfillment, reviews |
| Social app | auth, profiles, feed, messaging, notifications |
| Todo / task app | auth, tasks |
| CMS | auth, content, media, publishing, subscriptions |
| Data platform | ingestion, processing, storage, api, reporting |

**Rules:**
- Minimum 1 domain (even the simplest apps have at least one)
- Maximum 8 domains (if you find more, merge related ones)
- Auth is almost always its own domain
- Shared utilities (logging, config, error handling) are a cross-cutting concern, not a domain — note them separately
- If two feature areas always change together in the git log, they should be the same domain
- If a feature area has its own database tables, it is likely its own domain

---

## Analysis Steps

### Step 1 — List candidate domains

From the discovery files, list every distinct feature area you can identify. For each:
- Name it
- List the source files that belong to it
- List the database entities it owns
- List the API routes it handles

### Step 2 — Check coupling

For each pair of candidate domains:
- Do they share database tables? (if yes, consider merging or defining ownership)
- Do they call each other directly? (if yes, define the interface)
- Do they always deploy together? (if yes, consider merging)

### Step 3 — Assign execution order

Some domains must be built before others. Identify the dependency graph:
- Which domain has the foundational data model (usually auth or users)?
- Which domains depend on auth being complete?
- Which domains are fully independent of each other?

---

## Output: `discovery/domain-map.md`

Write this file with the following structure:

```markdown
# Domain Map

## Summary

Total domains identified: N
Execution strategy: sequential | parallel | mixed

## Domains

### Domain: {name}

**Description**: One sentence describing this domain's responsibility.

**Source files**:
- `relative/path/to/file.ts` — what it does
- ...

**Owns these data entities**:
- `EntityName` — brief description

**API surface**:
- `GET /path` — description
- `POST /path` — description

**Dependencies**: 
- Depends on: [other-domain-name] (reason)
- Required by: [other-domain-name] (reason)

**Risk level**: LOW | MEDIUM | HIGH
**Risk notes**: Why this domain is risky to migrate (based on hot files, bug history, complexity)

---

(repeat for each domain)

## Cross-Cutting Concerns

List any utilities, middleware, or infrastructure that spans multiple domains:
- `concern-name` — what it is and how to handle it (usually migrated as shared lib before domains)

## Execution Order

```
Phase A (must complete first — foundational):
  - domain-name

Phase B (can run in parallel after Phase A):
  - domain-name
  - domain-name

Phase C (can run in parallel after Phase B):
  - domain-name
```

## Migration Notes

Any project-wide observations that affect all domains:
- Authentication approach changes
- Data migration strategy
- Feature flags recommended
- Known legacy tech debt to not carry forward
```

---

## Completion

After writing `discovery/domain-map.md`, print:

```
[DOMAIN DECOMPOSE COMPLETE]
Domains identified: {comma-separated list}
Execution order: {Phase A: ..., Phase B: ..., ...}
File written: discovery/domain-map.md
```

Do not proceed to any other phase. Your job ends here.
