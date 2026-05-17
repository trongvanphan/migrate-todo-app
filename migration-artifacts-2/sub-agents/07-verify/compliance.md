# Sub-Agent: Verify — Compliance

You verify the implementation satisfies the regulatory scope in `parameters.COMPLIANCE_SCOPE`.

This dimension is **mandatory** for any domain handling regulated data. Missed controls have legal consequences.

---

## Parameters

- `{{DOMAIN}}`
- `parameters.COMPLIANCE_SCOPE` from state (one of: `none | gdpr | soc2 | hipaa | pci | iso27001`, or a combination)

---

## Output Files

- `domains/{{DOMAIN}}/verify-compliance.md`

---

## Per-Regime Checks

### GDPR

- PII columns tagged in `data-migration.md` schema mapping
- Delete-flow exists: a user can request deletion; verify a `DELETE /me` or admin endpoint cascades correctly:
  ```bash
  grep -rn "rightToErasure\|deleteUser\|gdpr.*delete\|DELETE.*user" {{OUTPUT_PATH}}/{{DOMAIN}} 2>/dev/null
  ```
- Audit log entry on every PII access
- Export-flow exists (data portability)
- Cookie / consent banner (if user-facing)
- Data residency: confirm storage region per spec

### SOC2

- Audit log: every state-changing operation logs actor + before/after
  ```bash
  grep -rn "audit\.\|auditLog\|emitAudit" {{OUTPUT_PATH}}/{{DOMAIN}} 2>/dev/null
  ```
- Access control: role-based; least privilege
- Change management: every deploy traceable to a PR
- Backups: verified per data-migration.md
- Vendor management list updated if new third parties introduced

### HIPAA

- All PHI encrypted at rest and in transit
- BAAs in place with any new vendor
- Access log for every PHI read (not just write)
- Audit log retention ≥ 6 years

### PCI-DSS

- Card data tokenized; no raw PAN in app DB
  ```bash
  grep -rn "creditcard\|cc_number\|cvv\|card_pan" {{OUTPUT_PATH}}/{{DOMAIN}} -i 2>/dev/null | grep -v __tests__
  ```
- PAN masking in logs (last 4 only)
- Network segmentation per design
- Quarterly scans scheduled
- Key rotation procedure documented

### ISO 27001

- Risk register entries map to controls
- Asset inventory updated
- Incident response runbook references this domain

---

## Cross-cutting

- Data classification labels in code (e.g., `@pii`, `@phi`, `@card-data` annotations)
- Encryption: at rest (DB + backups), in transit (TLS 1.2+), envelope encryption for sensitive fields

---

## Finding Levels

- CRITICAL: regulated data unencrypted, no audit log on PII access, raw PAN in code
- HIGH: missing delete/export flow, audit retention insufficient, missing access controls
- MEDIUM: insufficient logging coverage, missing data classification annotations
- LOW: doc/runbook gaps

---

## Output

```markdown
# Verify — Compliance — {{DOMAIN}}

**Scope**: {parameters.COMPLIANCE_SCOPE}

## Controls matrix
| Regime | Control | Status | Evidence path |
|--------|---------|--------|---------------|
| GDPR | Right to erasure | PASS | api/me.delete.ts |
| GDPR | Data portability | FAIL | (missing export endpoint) |
| SOC2 | Audit log on write | PASS | infra/audit.ts |
| PCI  | PAN tokenization | PASS | adapters/payments-tokenizer.ts |
| PCI  | PAN masking in logs | FAIL | logs leak last 8 in error path |

## Findings (COMPL-NNN)

### COMPL-001 (CRITICAL): PAN visible in error logs
**Evidence**: services/charge.ts:142
**Fix**: redact via logger middleware before emit
**Regulator impact**: PCI 3.4
```

---

## Completion

```
[VERIFY-COMPLIANCE: {{DOMAIN}}]
Scope: {scope}
PASS: {N}, FAIL: {N}
File: domains/{{DOMAIN}}/verify-compliance.md

HUMAN GATE: security/compliance review required before ramp >10%.
```
