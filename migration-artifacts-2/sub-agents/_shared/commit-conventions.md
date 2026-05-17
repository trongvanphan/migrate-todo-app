# Commit Conventions

All commits during migration must follow these rules. Enforced by `05-execute/bundle-execute.md` and verified by `07-verify/code-quality.md`.

---

## Commit Message Format

```
<type>(<domain>)[<bundle>]: <subject>

<body>

<footer>
```

- **type**: `feat | fix | refactor | test | docs | chore | perf | sec | data`
- **domain**: lowercase domain name from `domains/_index.md`
- **bundle**: optional, `BUNDLE-N` for execute-phase commits
- **subject**: imperative, ≤72 chars, no trailing period
- **body**: what + why (not how). Reference FR-N / AC-N when applicable.
- **footer**: `Co-Authored-By: ...`, `Refs: spec-driven/{domain}/spec.md#FR-3`

### Examples

```
feat(auth)[BUNDLE-2]: add OIDC token verification middleware

Implements FR-3.1 and FR-3.2 from auth spec. Validates RS256 signatures
against rotating JWKS; caches keys for 10 minutes.

Refs: domains/auth/spec.md#FR-3
Co-Authored-By: Claude Sonnet 4.6 (1M context) <noreply@anthropic.com>
```

```
sec(payments): redact PAN from request logs

Fixes verify finding COMPL-007 (PCI-DSS 3.4). Pads all 16-digit card
numbers in request body before structured log emission.

Refs: domains/payments/verify-compliance.md#COMPL-007
```

---

## Branch Naming

```
migration/{domain}                   — integration branch (long-lived)
migration/{domain}/bundle-{N}        — bundle integration
migration/{domain}/bundle-{N}/{slug} — individual feature work
hotfix/{domain}/{slug}               — production hotfixes
```

Never commit directly to `main` or `migration/{domain}`. Always PR.

---

## PR Title

`<type>(<domain>): <subject>` — match the commit message subject.

## PR Body Template

```markdown
## Summary
{1-3 bullets}

## FRs implemented
- FR-N.M (refs spec-driven/{domain}/spec.md)

## Bundle
BUNDLE-{N} (of M for this domain)

## Test plan
- [ ] Unit tests pass: `npm test -- {domain}`
- [ ] Lint clean
- [ ] Type check clean
- [ ] Manual smoke

## Risk + rollback
{paste relevant section from rollback-runbook.md}
```

---

## Tag Format

After each domain reaches 100% canary:
```
git tag migration/{domain}/100pct-$(date +%Y%m%d)
```

After decommission:
```
git tag migration/{domain}/decommissioned-$(date +%Y%m%d)
```

---

## What Must Never Be Committed

- `.env`, `.env.*` (except `.env.example`)
- `credentials.json`, service-account keys, certificates
- Large binaries (>1MB) unless declared in `.gitattributes` LFS
- Generated code without a `// GENERATED — DO NOT EDIT` header
- IDE config (`.idea/`, `.vscode/settings.json`) — these go in user gitignore
