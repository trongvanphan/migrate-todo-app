# Sub-Agent: Data Migration Design

You design the data migration plan for `{{DOMAIN}}`: schema diff, backfill, dual-write window, cutover. Required for any domain that owns persistent data.

---

## Parameters

- `{{DOMAIN}}`

---

## Output Files

- `domains/{{DOMAIN}}/data-migration.md` (≤2000 lines)
- `domains/{{DOMAIN}}/data-migration/` directory with placeholder scripts:
  - `01-schema-diff.sql` (or migration tool equivalent)
  - `02-backfill.sql`
  - `03-dual-write-enable.md`
  - `04-cutover.md`
  - `05-reconcile.sql`
  - `06-archive.md`

---

## Context Budget

Read `discovery/schemas/*-schema.md` for the prefixes owned by this domain (per charter) + `domains/{{DOMAIN}}/design.md`.

---

## Sections

```markdown
# Data Migration — {{DOMAIN}}

## Legacy data ownership

| Table/Collection | Rows (est) | Size | PII? | Notes |
|------------------|------------|------|------|-------|

## Target data model

| New table/collection | Source legacy | Transformation |
|----------------------|---------------|----------------|

## Schema diff

```sql
-- Columns added
ALTER TABLE new_users ADD COLUMN email_verified_at TIMESTAMPTZ;

-- Columns dropped (must be unused per discovery)
-- (legacy `old_field` is not referenced; safe to drop after cutover)

-- Type changes (require backfill transform)
-- legacy.amount BIGINT (cents) → new.amount NUMERIC(19,4)
```

## Backfill plan

**Strategy**: bulk + delta CDC

1. **Bulk** (one-time): snapshot legacy table → transform → load into new.
   - Tooling: AWS DMS | Debezium | custom Python
   - Expected duration: {hours}
   - Validation: row count diff = 0; sample 1000 rows for value equality
2. **Delta**: CDC stream from legacy to new during dual-write window.
   - Tooling: Debezium → Kafka → consumer in new system

## Dual-write window

Duration: **30 days minimum**.

During this period:
- Legacy is the source of truth.
- Every write to legacy is mirrored to new via CDC.
- New system reads can be served at increasing canary %.
- Reconciliation job runs nightly, diff < 0.01%.

## Cutover

1. Reach 100% read traffic on new (canary complete).
2. Run final reconciliation; require zero unexplained diff.
3. Switch write source of truth: new system writes primary, legacy receives via reverse CDC for 30 more days.
4. After 30 days, disable reverse CDC.
5. After 60 days of stable single-source, proceed to archival (Phase 09).

## Reconciliation script (sketch)

```sql
-- 05-reconcile.sql
WITH legacy AS (SELECT id, hash_md5(row_to_json(t)::text) AS h FROM legacy_schema.users t),
     new AS    (SELECT id, hash_md5(row_to_json(t)::text) AS h FROM new_schema.users t)
SELECT 'missing_in_new' AS kind, l.id FROM legacy l LEFT JOIN new n USING (id) WHERE n.id IS NULL
UNION ALL
SELECT 'missing_in_legacy', n.id FROM new n LEFT JOIN legacy l USING (id) WHERE l.id IS NULL
UNION ALL
SELECT 'value_drift', l.id FROM legacy l JOIN new n USING (id) WHERE l.h != n.h
LIMIT 1000;
```

## Rollback (data)

If new system is rolled back:
- CDC continues legacy → new during the rollback window (no data loss).
- If reverse CDC was active, replay any new-system writes to legacy from Kafka offset.
- See `_shared/rollback-runbook-template.md` Level 4.

## PII handling

- Columns with PII (per `discovery/schemas/*` PII flags): apply field-level encryption in new schema if `parameters.COMPLIANCE_SCOPE` includes GDPR/HIPAA.
- Audit log every read of PII columns.

## Open risks

- R-{id}: {risk}
```

---

## Completion

```
[DATA-MIGRATION-DESIGN COMPLETE: {{DOMAIN}}]
Tables: {N}, Backfill jobs: {N}, Dual-write window: {days}
Files: domains/{{DOMAIN}}/data-migration.md + data-migration/ scripts

HUMAN GATE: data engineering review before Phase 04.
```
