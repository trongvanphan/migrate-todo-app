---
domain_slug: <slug>          # lowercase-with-hyphens, [a-z0-9-]+, ≤64 chars
status: draft                 # draft | final
written_by: migration-artifacts-2 / Phase 01
---

# Legacy Context — <Domain Name>

> This file is the briefing that `/sds.spec --from migration/domains/<slug>/legacy-context.md --draft` will consume. It carries **legacy-side** knowledge — what the existing system does today — so the new spec can be drafted against accurate context.

## Source repositories

| Repo | Path | Branch | Role |
|---|---|---|---|
| <repo-name> | <abs path or remote> | <branch> | <primary / shared kernel / data> |

If single-repo, list only one row.

## Source paths in the legacy app

- `<legacy/path/one>` — <one-line purpose>
- `<legacy/path/two>` — <one-line purpose>

## User-facing surface

| Surface kind | Identifier | Notes |
|---|---|---|
| Route | `/path` | <auth/anon, purpose> |
| Screen | <ScreenName> | <user task> |
| Job | <job-name> | <schedule, side effect> |

## API surface

| Method | Path | Auth | Request | Response | Owner today |
|---|---|---|---|---|---|
| GET | /tasks | Bearer | – | Task[] | <module> |

Include legacy quirks — non-RESTful naming, undocumented headers, response envelopes — and call them out as **carry-over** or **drop**.

## Data model

For each table or document collection:

- Name, primary key, indexes
- Columns/fields with types and nullability
- Retention rules
- PII / sensitivity tags

## Cross-domain dependencies

| Direction | Other domain | Contract | Notes |
|---|---|---|---|
| Consumes | <other-slug> | <contract-name>@<ver> | <why> |
| Provides | – | <contract-name>@<ver> | <consumers> |

## Constraints

- Compliance: <list from `COMPLIANCE_SCOPE`>
- Performance baseline: <legacy p95, throughput>
- Integration: <external systems hit today>
- Operational: <oncall pager, runbook locations>

## Explicit out-of-scope

Things the user already said are NOT part of the migration for this domain. Be specific.

- <e.g. "Social OAuth providers — replaced with email+password in v1">
- <e.g. "Offline / service-worker caching — dropped">

## Migration risks

Identified during Phase 01 decomposition. Each will be re-evaluated in `/sds.spec` and `/sds.design`.

- **R-<n>** (severity): <one-line description>

## Notes for `/sds.spec --draft`

Free-form notes the spec drafter should weight heavily. Keep terse.

- <e.g. "Tasks are isolated per user — security rule in legacy is `auth.uid === $uid`; the new spec must preserve this invariant.">
- <e.g. "Filter is server-side via `orderByChild('completed')`. New API must keep filter on the server, not in the client.">
