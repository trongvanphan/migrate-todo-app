# Sub-Agent: Verify — Data Parity

You compare data between legacy and new at row level for `{{DOMAIN}}`'s tables. Drift = silent failure of the dual-write window.

---

## Parameters

- `{{DOMAIN}}`

---

## Output Files

- `domains/{{DOMAIN}}/verify-data-parity.md`
- `domains/{{DOMAIN}}/data-migration/parity-results.json`

---

## Procedure

1. Read `domains/{{DOMAIN}}/data-migration.md` for table mappings.
2. For each pair (legacy_table, new_table):
   - Sample 10,000 rows by primary key range.
   - Hash each row (excluding nondeterministic fields per `08-api-diff/semantic-equivalence.md` rules).
   - Diff: count missing-in-new, missing-in-legacy, value-drift.
3. Also run total row count comparison.

---

## Reconciliation query template

Use `domains/{{DOMAIN}}/data-migration/05-reconcile.sql` from Phase 03. Run; capture results.

---

## Allowed drift

During dual-write window, allowed drift is:
- ≤ 0.01% missing-in-new (CDC catching up)
- 0 missing-in-legacy (legacy is source of truth)
- ≤ 0.001% value-drift (rounding from type conversions, e.g., float→decimal)

After cutover, allowed drift drops to zero.

---

## Output

```markdown
# Verify — Data Parity — {{DOMAIN}}

## Tables
| Legacy table | New table | Legacy rows | New rows | Missing in new | Missing in legacy | Value drift |
|--------------|-----------|-------------|----------|-----------------|--------------------|-------------|
| legacy.users | new.users | 1_200_345 | 1_200_338 | 7 (0.0006%) | 0 | 12 (0.001%) |

## Drift details (sample)
| Kind | Row PK | Field | Legacy value | New value | Hypothesis |
|------|--------|-------|--------------|-----------|------------|
| value_drift | 4815 | created_at | 2022-01-01 00:00:00+00 | 2022-01-01 00:00:00.001+00 | timestamp precision |

## Findings (DP-NNN)
```

---

## Finding Levels

- CRITICAL: >1% drift, any missing-in-legacy, drift on financial/PII fields
- HIGH: drift on user-visible fields, missing-in-new >0.1% sustained
- MEDIUM: drift on derived fields, type-precision differences
- LOW: timestamp precision drift on internal fields

---

## Completion

```
[VERIFY-DATA-PARITY: {{DOMAIN}}]
Drift summary: missing-new={x}, missing-legacy={y}, value-drift={z}
File: domains/{{DOMAIN}}/verify-data-parity.md
```
