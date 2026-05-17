# Sub-Agent: Decommission — Data Archival

Gate 3. Snapshot legacy data to cold storage, then disconnect writes. Pre-condition for removing legacy DB resources.

---

## Parameters

- `{{DOMAIN}}`

---

## Output Files

- `decommission/{{DOMAIN}}/archive-plan.md`
- `decommission/{{DOMAIN}}/archive/manifest.json` (after archival completes)

---

## Context Budget

See `sub-agents/_shared/context-budget-rules.md`. Read only the inputs explicitly listed in Parameters; do not load full discovery dumps.

---

## Procedure

### 1. Plan

From `domains/{{DOMAIN}}/data-migration.md`, list legacy tables owned by this domain.

For each:
- Estimate size.
- Determine retention policy (legal, regulatory, business — confirm with data eng + legal).
- Choose target: S3 Glacier, GCS Coldline, Azure Archive, or on-prem cold storage.

### 2. Snapshot

```bash
# Postgres example
pg_dump --no-owner --no-acl --format=custom \
  --table="legacy.{{DOMAIN}}_*" \
  $LEGACY_DB_URL > /tmp/{{DOMAIN}}-final.dump

# Encrypt
gpg --encrypt --recipient ops@org.com -o /tmp/{{DOMAIN}}-final.dump.gpg /tmp/{{DOMAIN}}-final.dump

# Upload to cold storage
aws s3 cp /tmp/{{DOMAIN}}-final.dump.gpg \
  s3://org-cold-archive/migrations/{{DOMAIN}}/$(date +%Y%m%d)/ \
  --storage-class GLACIER

# Verify
aws s3 ls s3://org-cold-archive/migrations/{{DOMAIN}}/$(date +%Y%m%d)/
```

### 3. Disconnect writes

```sql
-- Make legacy tables read-only at the DB level
REVOKE INSERT, UPDATE, DELETE ON legacy.{{DOMAIN}}_users FROM application;
REVOKE INSERT, UPDATE, DELETE ON legacy.{{DOMAIN}}_orders FROM application;
-- ...
```

Also disable any CDC stream from legacy to new (no longer needed at 100% canary).

### 4. Manifest

```json
{
  "domain": "{{DOMAIN}}",
  "archived_at": "{ISO}",
  "tables": [
    {
      "name": "legacy.{{DOMAIN}}_users",
      "rows": 1200345,
      "size_bytes": 4_823_000_000,
      "snapshot_path": "s3://org-cold-archive/migrations/{{DOMAIN}}/20260301/{{DOMAIN}}-final.dump.gpg",
      "checksum_sha256": "...",
      "encryption": "gpg",
      "retention_until": "2033-03-01"
    }
  ],
  "writes_disconnected": true,
  "cdc_disabled": true,
  "verified_by": "data-eng-oncall"
}
```

---

## Output (plan)

```markdown
# Decommission Gate 3 — Data Archival Plan — {{DOMAIN}}

| Table | Rows | Size | Retention | Target | Status |
|-------|------|------|-----------|--------|--------|

## Procedure
1. Snapshot
2. Encrypt
3. Upload to cold storage
4. Verify checksum
5. Disconnect writes
6. Disable CDC

## Rollback (within window)
- For 30 days after archival, retain ability to restore from snapshot.
- After 30 days, snapshot becomes the only copy.
```

---

## State Update

```json
{
  "domains[{{DOMAIN}}].decommission_gate_3_archive": {
    "verified_at": "{ISO}",
    "manifest_path": "decommission/{{DOMAIN}}/archive/manifest.json",
    "result": "pass"
  }
}
```

---

## Completion

```
[DECOMMISSION-DATA-ARCHIVAL: {{DOMAIN}}]
Tables archived: {N}, total size: {GB}
Manifest: decommission/{{DOMAIN}}/archive/manifest.json

HUMAN GATE: data eng + legal sign-off on retention policy.
```
