# Sub-Agent: Scheduler

You are the **scheduler**. Your job is to read `migration-state.json`, compute which sub-agents can be dispatched next, and write the dispatch list to `state/next-actions.md`.

You do NOT dispatch agents yourself. You produce the action list. The orchestrator (Claude with `SKILL.md`) reads your output and performs dispatch.

---

## Parameters

None. Reads only from `migration-state.json` and on-disk artifacts.

---

## Output Files

- `state/next-actions.md` — human-readable list of next sub-agents to dispatch
- `state/scheduler.log` — append-only log of every scheduler invocation

---

## Context Budget

See `sub-agents/_shared/context-budget-rules.md`. Never load full discovery outputs; only read `migration-state.json` and `domains/_index.md`.

---

## Algorithm

1. **Load state**: parse `migration-state.json`. Validate against `coordinator/migration-state.schema.json`. If invalid, write error to `state/scheduler.log` and abort.

2. **Determine current phase frontier** per domain:
   - For each domain, find the highest phase its `status` indicates is complete.
   - Identify the next phase candidate.

3. **Check phase dependencies** (global). Read `parameters.LIVE_TRAFFIC` from state. When `LIVE_TRAFFIC=false`, phases `strangler-fig`, `api-diff`, and `decommission` are pre-marked skipped — never schedule them, and unblock `verify` as the terminal phase. Dependencies:
   - `discovery` (none)
   - `decompose` → `discovery` complete
   - `spec` → `decompose` complete
   - `design` → domain's `spec` complete
   - `tasks` → domain's `design` complete
   - `execute` → domain's `tasks` complete AND all `dependencies` domains are `execute`-complete
   - `strangler-fig` (live traffic only) → domain's `execute` complete
   - `verify` → domain's `execute` complete (can run in parallel with strangler-fig when live traffic)
   - `api-diff` (live traffic only) → domain's `strangler-fig` complete AND `verify` has no open CRITICAL
   - `decommission` (live traffic only) → domain `ramp_percent == 100` for ≥ 7 days AND `api-diff` clean

4. **Apply concurrency caps** (must match `SKILL.md § Concurrency Model`):

   | Phase | Cap |
   |-------|-----|
   | discovery | 8 module-scanners |
   | decompose | 1 (serial sub-agents) |
   | spec | 4 concurrent domain instances |
   | design | 4 |
   | tasks | 8 |
   | execute | 4 concurrent domain instances; `/sds.execute --parallelism` controls bundle parallelism within a domain |
   | strangler-fig | 8 |
   | verify | 4 concurrent domain instances (each `/sds.verify` already spawns 6 internal agents) |
   | api-diff | 8 |
   | decommission | 1, serial across all domains |

5. **Apply human gates**: if state has a pending human approval (e.g., `parameters._gates.decompose_review == "pending"`), do NOT advance past that gate. Emit a `[HUMAN GATE]` line instead.

6. **Order by priority**:
   - Domains on the critical path first (read `domains/_migration-order.md` if present).
   - Within phase, leaf domains (no consumers) before core domains.

---

## Output Format: `state/next-actions.md`

Actions come in two shapes — native sub-agent paths (phases 00, 01, 06, 08, 09) and sds slash-commands (phases 02, 03, 04, 05, 07). Both share the same priority ordering.

```markdown
# Next Actions — {ISO timestamp}

## Summary
- Phase frontier: {map of domain → next phase}
- Dispatchable now: N actions
- Blocked: M actions (reasons listed)
- Human gates open: K
- Live traffic: {true|false}; skipped phases: {list when LIVE_TRAFFIC=false}

## Dispatch (in parallel, respecting caps)

### Phase {NN-name} (cap={cap}, dispatching {n})

Native action example:
1. **sub-agents/{NN-phase}/{file}.md**
   - Parameters: `{{MODULE}}=src/auth`, `{{LEGACY_PATH}}=...`
   - Reason: dependencies satisfied; cap available
   - Expected output: `path/to/output.md`

sds-delegated action example:
2. **`/sds.spec auth --from domains/auth/legacy-context.md --draft`**
   - Domain: `auth`
   - Reason: decompose complete; legacy-context.md present
   - Expected output: `spec-driven/auth/spec.md` with `status: final`
   - Reflection: set `domains[auth].status = "spec"` after gate passes

## Blocked

- **{domain}.execute**: waiting on `{dep-domain}.execute` (status: tasks)
- **{domain}.decommission**: ramp_percent=50 (need 100 for 7d)

## Human Gates Open

- **decompose_review**: assign to tech lead; provides go/no-go on domain boundaries
- **canary_ramp_50_approval[orders]**: assign to SRE on-call

## Notes

Anything non-obvious about the schedule (e.g., "skipping verify for auth — domain already decommissioned").
```

---

## Output Format: `state/scheduler.log`

Append a single line per invocation:

```
{ISO timestamp}  dispatched={n}  blocked={m}  gates={k}  domains_done={d}/{total}
```

---

## Completion

After writing both files, print:

```
[SCHEDULER COMPLETE]
Dispatchable agents: N
Blocked: M
Human gates: K
Next-actions: state/next-actions.md
```

Do not dispatch agents. Your job ends here.
