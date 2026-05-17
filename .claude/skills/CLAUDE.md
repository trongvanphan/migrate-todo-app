# Skill Development

## Design Principle Consistency

Read `../docs/design-rationale.md`. All skills in this directory should be consistent with those principles, unless doing so would create a suboptimal solution or design. If this occurs, always surface to the user for clarification rather than making a decision, so that the user can use their greater context to provide the correct direction.

All skills should follow these constraints - perform a second scan / double-check of the skill after finalizing any edits against it:

## Structure

- **SKILL.md under 500 lines.** Move domain content to reference files. One level of reference depth (SKILL.md → file, not SKILL.md → file → file).
- **Every conditional has all branches defined.** If/else, switch/default, flag present/absent — no implicit "do nothing" paths.
- **Every flag in the Arguments table appears in the pipeline body.** Every flag combination either has explicit handling or explicit mutual exclusion.
- **All file path references resolve.** Relative paths must work from the skill's directory. Test with fresh checkout.
- **Pass paths to subagents, not content.** Subagents read files independently. Embedding file content in prompts wastes tokens and introduces orchestrator bias.
- **Frontmatter**: `name` is lowercase-with-hyphens (≤64 chars). `description` is third-person, has trigger phrases, describes what not how (≤1024 chars). Do not use `allowed-tools` — it is a non-standard, experimental Claude Code extension that only narrows tool access. Skills need full tool access; narrowing adds no value and reduces cross-platform portability.

## Clarity

- **Imperative voice for actions.** "Read the file at X" not "The file should be read" or "Consider reading."
- **Declarative voice for rules.** "Validation is advisory, never blocking" — stated as fact, no qualifiers on invariants.
- **One term per concept.** Don't alternate between "dimension registry" and "discovered dimensions" for the same data structure.
- **Negative constraints are prominent.** "NEVER proceed without validation" at the start of a section or in a dedicated block — not buried in paragraph 3.
- **Constraints at point of action.** A constraint in a centralized block AND reinforced where the action happens. Don't rely on the model remembering a rule from 100 lines ago.
- **Pronouns have unambiguous antecedents.** "Run the script. If it fails..." — "it" clearly refers to "the script." Avoid "it" when two plausible referents exist.
- **High-fragility operations = low freedom.** File writes, git commands, destructive operations get exact commands. Analysis and review allow model judgment.
- **Sequence dependencies are explicit.** "MUST complete before" or "Launch in parallel" — never rely on document position alone.

## Edge Cases

- **Every error path reaches a terminal state.** No dangling "if validation fails" without defined recovery or stop.
- **Retries are bounded.** "Retry once, then exclude" not "retry until success."
- **Subagent failures have fallbacks.** Timeout, error, partial results — each has defined behavior.
- **Shell commands quote paths.** `"$path"` not `$path`. Handle spaces and special characters.
- **State persistence is explicit.** Single-session? State it. Mid-execution interruption? State the cleanup.
- **Directory scans are scoped.** Filter before consumption — don't glob `**/*` and hope for the best.

## Contracts

- **Input format is specified.** Every external artifact consumed has defined structure (file format, required fields, path conventions).
- **Output format is specified.** Every artifact produced has defined structure, destination path, and naming convention.
- **IDs are parseable.** `PREFIX-N` patterns are consistent. Adjacent skills in a pipeline agree on ID formats.
- **Paths are predictable.** The skill doesn't contradict itself on where files go. Absolute paths for subagent prompts.
- **Internal self-consistency.** Output descriptions match input parsing. Templates match generation instructions. Argument defaults in the table match pipeline body handling.

## Model Adherence

- **Progress signals every 3–5 steps.** Log statements, checkpoints, or verification gates. Long non-interactive stretches cause drift.
- **Emphasis is rare.** CRITICAL/MUST/MANDATORY used sparingly — if >20% of instructions have emphasis, none of it registers.
- **Verification before proceeding.** Multi-step processes have at least one checkpoint. "Verify the file exists and is non-empty" before moving to the next stage.
- **Motivate restrictions.** "Do not modify the target — the user reviews and applies all changes, and modification would corrupt re-run comparability" is stronger than "Do not modify the target."
- **Literal interpretation works.** Instructions produce correct behavior when followed literally. "Read the file" not "Process the input." Specific verbs, concrete objects, explicit scope.
- **All text serves the executing model.** No design rationale, maintainer commentary, or "how to extend" guidance in SKILL.md — that belongs in docs/.
- **Tables under 10 rows.** Larger tables need explicit "process every row" instructions. Place tables near their point of use.
