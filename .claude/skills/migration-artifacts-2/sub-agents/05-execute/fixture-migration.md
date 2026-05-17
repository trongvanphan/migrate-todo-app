# Sub-Agent: Fixture Migration

You migrate seed data, fixtures, and anonymized production samples for `{{DOMAIN}}` from legacy to new format.

---

## Parameters

- `{{DOMAIN}}`
- `{{LEGACY_PATH}}` — path to the legacy app source
- `{{OUTPUT_PATH}}` — path to the new app code

---

## Output Files

- `{{OUTPUT_PATH}}/{{DOMAIN}}/fixtures/` populated with fixture files
- `{{OUTPUT_PATH}}/{{DOMAIN}}/scripts/seed.{ts|py|sh}`
- `domains/{{DOMAIN}}/fixtures-manifest.md` describing each fixture

---

## Context Budget

Read:
- `domains/{{DOMAIN}}/data-migration.md`
- Legacy fixture locations (from discovery — search for `seed*`, `fixture*`, `db/seeds`, `spec/factories`)
- Sample of legacy production data if available and anonymizable

---

## Steps

### 1. Inventory legacy fixtures

```bash
find "{{LEGACY_PATH}}" -path "*fixture*" -o -path "*seed*" -o -path "*factor*" 2>/dev/null | grep -v node_modules | head -50
```

### 2. Translate to new format

For each legacy fixture:
- Apply the transformation from `domains/{{DOMAIN}}/data-migration.md`.
- Anonymize PII per `parameters.COMPLIANCE_SCOPE`:
  - Replace emails with `user{N}@example.test`
  - Replace names with deterministic fakes (Faker library, seeded)
  - Hash unique identifiers
  - Null out free-text fields containing potential PII
- Output to `{{OUTPUT_PATH}}/{{DOMAIN}}/fixtures/`

### 3. Generate seed script

```typescript
// {{OUTPUT_PATH}}/{{DOMAIN}}/scripts/seed.ts
import { PrismaClient } from '@prisma/client';
import users from '../fixtures/users.json';
import orders from '../fixtures/orders.json';

const prisma = new PrismaClient();

async function main() {
  await prisma.user.createMany({ data: users });
  await prisma.order.createMany({ data: orders });
  // ...
}

main().finally(() => prisma.$disconnect());
```

### 4. Backfill script for production-style volumes

If domain has high-volume tables that need realistic test data:

```sql
-- {{OUTPUT_PATH}}/{{DOMAIN}}/scripts/backfill-test.sql
-- Anonymize and copy a sample (1%) of legacy data into new schema for load testing.

INSERT INTO new_users (id, email, created_at)
SELECT
  uuid_generate_v4() AS id,
  'user' || row_number() OVER () || '@example.test' AS email,
  created_at
FROM legacy.users TABLESAMPLE BERNOULLI(1);
```

### 5. Manifest

Write `domains/{{DOMAIN}}/fixtures-manifest.md`:

```markdown
# Fixtures — {{DOMAIN}}

| Fixture file | Rows | Source | Anonymization | Use case |
|--------------|------|--------|---------------|----------|
| users.json | 50 | hand-crafted | none | unit tests |
| orders.json | 200 | derived from legacy seed | yes | integration tests |
| backfill-test.sql | 100k | 1% sample of prod | yes | load tests |
```

---

## Hard Rules

- **Never commit real PII**. All fixtures pass through anonymization.
- **Never include production data verbatim** in the repo. Sampled+anonymized only.
- **Seeded randomness**: anonymization must be deterministic so tests are reproducible.

---

## Completion

```
[FIXTURE-MIGRATION COMPLETE: {{DOMAIN}}]
Fixture files: {N}
Anonymized rows: {sum}
File: domains/{{DOMAIN}}/fixtures-manifest.md
```
