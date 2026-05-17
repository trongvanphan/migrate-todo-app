# Sub-Agent: DB Schema Scan (per prefix)

You scan database schema artifacts filtered by a **table-name prefix** (e.g., `auth_*`, `ord_*`). One agent per prefix. Multiple run in parallel.

---

## Parameters

- `{{LEGACY_PATH}}`
- `{{PREFIX}}` — regex matching tables/entities (e.g., `auth_`, `ord_`, `cust_`, or `.*` to do all once on a small app)

---

## Output Files

- `discovery/schemas/{{PREFIX}}-schema.md` (≤2000 lines)

---

## Context Budget

See `_shared/context-budget-rules.md`. If the schema has >100 tables matching the prefix, write summary + sample of 20 representative tables; reference the raw inventory.

---

## Scans

```bash
# Raw SQL migrations
find "{{LEGACY_PATH}}" -type f \( -name "*.sql" -o -path "*migrations*" \) -not -path "*/node_modules/*" 2>/dev/null | head -200

# Prisma schema
find "{{LEGACY_PATH}}" -name "schema.prisma" 2>/dev/null

# ORM entity files (TypeORM, JPA, ActiveRecord, SQLAlchemy, Mongoose, GORM)
grep -rln "@Entity\|@Table\|new Schema(\|mongoose\.model\|ActiveRecord::Base\|class.*Base\|declarative_base\|@Document\|gorm:" "{{LEGACY_PATH}}" --include="*.ts" --include="*.java" --include="*.py" --include="*.rb" --include="*.go" 2>/dev/null | grep -v node_modules | head -200

# DDL statements matching prefix
grep -rin "create table[[:space:]]\+{{PREFIX}}\|@Table.*{{PREFIX}}" "{{LEGACY_PATH}}" --include="*.sql" --include="*.java" --include="*.py" 2>/dev/null | head -100
```

---

## Output Structure

```markdown
# DB Schema — {{PREFIX}}

**Scanned at**: {ISO}
**DB engine**: {detected: postgres | mysql | oracle | mongodb | dynamo | firebase-rtdb | ...}
**Tables matching prefix**: {N}

## Tables (top 20 by importance)
| Table | Purpose (inferred) | Key columns | FKs | Indexes |
|-------|--------------------|-------------|-----|---------|

## Relationship map (FK edges)
```
{table_a} --(col)--> {table_b}
{table_a} --(col)--> {table_c}
```

## Data-access patterns observed
- By user_id: {tables}
- By time range: {tables}
- Full scan: {risky tables}

## PII columns (heuristic match: email, phone, ssn, dob, address, name, ip)
| Table.Column | Heuristic | Compliance flag |

## Migration risks
- Tables with no PK / no created_at: {list}
- Tables with `BLOB`/`TEXT` > 1KB avg: {list}
- Tables involved in dual-write candidates: {list}

## Volume estimate (if accessible)
| Table | Approx row count | Approx size |
```

---

## Completion

```
[DB-SCHEMA-SCAN COMPLETE: prefix={{PREFIX}}]
Tables: {N}, PII columns detected: {N}
File: discovery/schemas/{{PREFIX}}-schema.md
```
