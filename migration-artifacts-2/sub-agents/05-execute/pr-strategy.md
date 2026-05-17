# Sub-Agent: PR Strategy

You produce the per-domain branching and PR policy document. Runs ONCE per domain at the start of Phase 05.

---

## Parameters

- `{{DOMAIN}}`

---

## Output Files

- `domains/{{DOMAIN}}/pr-strategy.md`

---

## Content

```markdown
# PR Strategy — {{DOMAIN}}

## Branch structure

```
main
 └── migration/{{DOMAIN}}                      ← long-lived integration branch
      └── migration/{{DOMAIN}}/bundle-1/...    ← per-bundle work
      └── migration/{{DOMAIN}}/bundle-2/...
```

- `main` is sacred. Never push directly.
- `migration/{{DOMAIN}}` is the domain's integration branch. PRs from bundle branches merge here.
- After all bundles green + verify clean + canary at 100%, `migration/{{DOMAIN}}` merges to `main` via a release PR.

## Rebase policy

- Weekly: rebase `migration/{{DOMAIN}}` onto `main`.
- Before opening any bundle PR: rebase bundle branch onto current `migration/{{DOMAIN}}`.
- Never merge `main` into a bundle branch — always rebase.

## PR rules

1. **One bundle = one PR**.
2. **PR base = `migration/{{DOMAIN}}`**, not `main`.
3. **PR title format**: `feat({{DOMAIN}})[BUNDLE-N]: <subject>` (or `fix`, `refactor`, etc.).
4. **Required reviewers**: 1 from `{{DOMAIN}}` owner team + 1 from a backup team (avoids single-point-of-knowledge).
5. **Required checks**:
   - lint
   - typecheck
   - unit tests for `{{DOMAIN}}`
   - integration tests if bundle touches handlers
6. **Auto-merge**: enabled for bundles that touch only this domain. Disabled if the PR touches `lib/` (shared kernel).

## Hot-path approvals

If a bundle touches:
- Auth code → +1 from `security`
- Money/payments code → +1 from `payments-security`
- DB schema → +1 from `data-eng`

## Release PR (end of Phase 05)

When all bundles for `{{DOMAIN}}` are merged to `migration/{{DOMAIN}}`:
- Open `migration/{{DOMAIN}}` → `main` PR.
- Title: `release({{DOMAIN}}): merge to main (no traffic yet)`.
- Body lists every bundle PR + verify report status.
- **Merging to main does NOT route traffic.** Traffic routing is controlled by Phase 06 strangler-fig configs.

## Hotfix branches

If a hotfix is needed mid-migration:
- Branch from `main` (not `migration/{{DOMAIN}}`).
- Backport into `migration/{{DOMAIN}}` via rebase.
- Tag commits with `hotfix:` prefix per `_shared/commit-conventions.md`.
```

---

## Completion

```
[PR-STRATEGY COMPLETE: {{DOMAIN}}]
File: domains/{{DOMAIN}}/pr-strategy.md
```
