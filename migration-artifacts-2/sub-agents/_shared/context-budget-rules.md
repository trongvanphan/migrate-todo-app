# Context Budget Rules

Every sub-agent in v2 must follow these rules. Violating them causes context overflow, hallucination, or silent truncation at scale.

---

## Rule 1 — Bounded Input

- Operate on **one module / one domain / one feature / one schema-prefix at a time**.
- Never scan more than ~50K LOC in a single agent invocation.
- If your input parameters select more than 50K LOC, split the task and emit a directive to schedule additional invocations.

## Rule 2 — Bounded Output

- **Max 2000 lines per output file.** If your raw findings exceed this, write a summary + representative sample (≤20 examples per category) and reference the raw data location.
- Never paste full `grep -r` output. Aggregate first: counts, top-N, examples.
- Never paste full file contents. Quote ≤30 lines.

## Rule 3 — Bounded Search

- Always pass `--include=...` to grep. Never run an extension-less grep.
- Always use `find -maxdepth N` for tree walks. `N` should be the smallest value that covers your target.
- Always exclude `node_modules`, `.git`, `dist`, `build`, `target`, `vendor`, `.venv`, `__pycache__`.

## Rule 4 — Stream, Don't Accumulate

- Write per-module output files incrementally: `discovery/modules/{{MODULE}}/...`. Do not accumulate cross-module data in agent memory.
- Synthesis agents read **summaries only**, never raw scan outputs.

## Rule 5 — Handoff Via Files

- Pass context between phases through files in `state/handoff/{{PHASE}}/{{DOMAIN}}.json`, never via prompt-stuffing.
- The format is defined in `sub-agents/_shared/handoff-format.md`.
- If you need information another agent produced, read its handoff file. Do not re-derive it.

## Rule 6 — State File Discipline

- Read `migration-state.json` at start.
- Write back via atomic protocol:
  1. Read full state into memory.
  2. Modify in memory.
  3. Write to `migration-state.json.tmp`.
  4. `mv migration-state.json.tmp migration-state.json`.
- Never hold a write lock across long-running operations.

## Rule 7 — Fail Loudly

- If a precondition is missing (state file absent, required artifact missing), STOP and emit a clear error. Do not silently proceed.
- If an output exceeds budget, STOP and emit a directive to split the task. Do not truncate silently.

## Rule 8 — No Cross-Phase Re-Derivation

- If `domains/_index.md` exists, use it. Do not re-decompose.
- If `discovery/SUMMARY.md` exists, use it. Do not re-scan.
- Re-running an earlier phase is an explicit user action; agents must not do it on their own.

---

## Anti-Patterns to Avoid

- "Let me first read the entire codebase to understand it" — NO. Read the discovery summary.
- "I'll grep everything to make sure I don't miss anything" — NO. Bounded grep + summary.
- "I'll write a comprehensive file with all findings" — NO. ≤2000 lines, summary + sample.
- "I'll keep all the context in this conversation" — NO. Write to handoff files.

---

## Self-Check Before Writing Output

Ask yourself:
1. Did I bound my input to one logical unit?
2. Is my output ≤2000 lines?
3. Did I update `migration-state.json` atomically?
4. Did I write a handoff file for the next phase?
5. If something was too big, did I emit a split directive rather than truncate?

If any answer is "no", fix it before printing completion.
