# Spec Elicitation Guide

Detailed guidance for each phase of spec elicitation.

## Flexibility

Phases are guardrails, not walls. The user can steer the conversation in any direction — revisit earlier phases, skip ahead, dive deep on a single topic, or introduce context that doesn't fit neatly into a phase. Follow the user's lead. The phases exist to ensure nothing important is missed, not to enforce a rigid sequence.

## Interaction Policy

How user-facing questions are presented depends on the answer space. Apply these rules across all phases and adaptive flow paths.

**Structured input**: When the answer space is bounded — confirmations, yes/no, select-from-list, priority categorization, or any question where valid responses can be enumerated. Use the platform's interactive question or prompt mechanism to present options as selectable choices — not inline text.

**Free-form input** (conversational text): When the answer is genuinely open-ended — feature descriptions, problem statements, explanations, or editing instructions where the user expresses something in their own words.

**Hybrid** (structured input with free-form follow-up): When the primary answer is bounded but one option opens a free-text path (e.g., "Other: [specify]"). Present the initial choice as structured input; follow up conversationally if the user selects the free-text option.

**Tool-unavailable fallback**: If structured input is unavailable (tool error, not just untriggered), present options as a clearly formatted list with the instruction: "Reply with the number or name of your choice." A preference for plain text is not a valid reason to skip structured input.

**Supplementary rules:**

- **Never present bounded options as plain-text numbered or lettered lists.** If you are presenting choices for the user to select from — including clarification questions ("do you mean a or b?"), confirmation gates, and quality nudges — use structured input.
- **multiSelect vs single-select**: Use multiSelect when the user can legitimately choose more than one option simultaneously (e.g., user types, features to include). Use single-select for mutually exclusive choices.
- **Skip option**: Include a "Skip" choice when the question is optional or the answer might genuinely be unknown/TBD. Omit Skip for questions that gate subsequent phases.
- **Combined exchanges**: When combining multiple gap questions into one exchange, apply the mode rule per-question. A single exchange can mix structured input (for bounded sub-questions) with conversational text (for open-ended sub-questions).

---

## Scope Boundaries

**Spec elicitation focuses on WHAT, not HOW.**

Do NOT ask about:

- Tech stack choices (frameworks, libraries, languages)
- Implementation patterns (hooks vs classes, state management)
- Styling approaches (Tailwind, CSS modules, etc.)
- Architecture decisions (folder structure, API design)

If the user mentions tech stack in their description, acknowledge it briefly but don't probe further. Technical implementation decisions are out of scope for specification elicitation.

**Good spec question**: "What should users be able to do?"
**Bad spec question**: "What styling framework should we use?"

---

## Phase 0: Context Analysis (Always Runs)

**Goal**: Extract as much information as possible from available context before asking any questions.

### Context Source Priority

Process sources in this order:

1. **User's trigger message and inline text** — always available; extract intent, feature name, user types, goals, constraints
2. **Content from `--from` flag**:
   - Local file (e.g., `--from ./docs/prd.md`): read directly; supports markdown, plain text, and structured docs
   - URL matching a known MCP service (e.g., `ghe.coxautoinc.com`): use the corresponding MCP tool (e.g., `getGithubRepositoryContent`)
   - Other URL: fetch the URL content
   - Fetch failure: inform the user and ask them to paste the content directly
3. **Rally data** — if MCP tools are available and user opts in; offer import as part of this phase (see `references/rally-integration.md`)
4. **Codebase signals** — automatic when code exists; see Codebase Scan Rules below

### Session Continuation Detection

Before gathering fresh context, check for existing in-progress sessions:

1. Scan `spec-driven/.sessions/` for sidecar files matching `*.spec.json`
2. If found, read the sidecar to determine the feature slug and which phases were completed
3. Present a continuation offer (present as structured input per the Interaction Policy):

   ```
   I found an in-progress spec session: [feature name] ([slug])
   Phases completed: [list]

   Would you like to:
   - Continue from where you left off
   - Start fresh (this will discard the previous session)
   - Work on a different feature
   ```

4. If continuing, load the existing `spec-driven/<slug>/spec.md` as context and let the user steer from there — do not mechanically route to "Phase N"
5. If starting fresh, delete the old sidecar and proceed with normal Phase 0

**Sidecar file format**: `spec-driven/.sessions/<slug>.spec.json` containing:

- `slug`: the spec slug
- `featureName`: the feature name
- `phasesCompleted`: array of completed phase numbers
- `lastUpdated`: ISO timestamp
- `partialData`: any captured fields not yet written to the spec

Example:
```json
{
  "slug": "user-auth",
  "featureName": "User Authentication",
  "phasesCompleted": [0, 1],
  "lastUpdated": "2026-03-01T10:00:00Z",
  "partialData": {
    "overview": "...",
    "users": ["end-users", "admins"],
    "agentDecisions": []
  }
}
```

**Lifecycle**:

- Create the sidecar when Phase 1 begins (or when first substantive data is captured)
- Update after each phase completes
- Delete on final spec generation (the terminal action)
- If a sidecar is older than 7 days and the user starts a new invocation, treat it as stale — offer to discard or resume

**Incremental writes**: Write the spec file (`spec-driven/<slug>/spec.md`) incrementally after each phase completes, so content is preserved even if the session ends unexpectedly. The sidecar tracks which phases are complete; the spec file contains the actual content.

**Important**: Sidecar files are dotfile-hidden JSON, not markdown. They do not conflict with the "Do NOT read files in `spec-driven/`" rule, which applies to spec markdown files only.

**First-run container setup**: When the `spec-driven/` directory does not yet exist in the project, create it and perform one-time setup:

1. Create `spec-driven/README.md` with the content from [assets/container-readme.md](../assets/container-readme.md)
2. Check if the project's `.gitignore` covers `spec-driven/.sessions/`. If the entry is missing, add it:
   ```
   # Spec-driven workflow session files (ephemeral)
   spec-driven/.sessions/
   ```

This setup runs once per project. Subsequent skill invocations (spec, plan, task, execute) skip it if `spec-driven/README.md` already exists. The `.sessions/` gitignore entry covers all session files across all skills.

### Field Extraction Map

When parsing context sources, map patterns to spec template fields:

| Source Pattern                         | Maps To                       | Example                           |
| -------------------------------------- | ----------------------------- | --------------------------------- |
| "for [user type]" / "used by"          | Users > Primary Users         | "for product managers"            |
| "so that" / "in order to" / "because"  | Goals > Primary Goal          | "so teams can track work"         |
| "must not" / "won't" / "out of scope"  | Goals > Non-Goals             | "won't handle billing"            |
| "currently using" / "replaces"         | Dependencies                  | "replaces spreadsheet tracking"   |
| "currently" / "today" / "right now" / "existing" | Overview > Current State | "currently tracking in spreadsheets" |
| Numbered lists of capabilities         | Functional Requirements seeds | "1. Create tasks 2. Assign tasks" |
| Given/When/Then or acceptance criteria | FR Acceptance Criteria        | "Given a user is logged in..."    |

### Gap Analysis Output Format

After processing all available context, present:

```
Here's what I gathered from your input:
- Feature: [extracted]
- Problem: [extracted]
- Users: [extracted or "not yet identified"]
- Scope signals: [extracted or "none detected"]
- Constraints: [extracted or "none detected"]

I still need to understand:
- [gap 1]
- [gap 2]
```

### Draft Mode

When `--draft` is passed explicitly OR Context Analysis covers all Phase 1+2+3 questions without meaningful gaps:

- Generate a draft spec from the extracted context
- Present for validation: "Here's a draft spec from your input. Review each section — I'll ask about anything I had to infer."
- Provenance markers (`[User]`, `[Inferred]`, `[Rally]`, etc.) are included inline and are permanent — do not strip them

**Confidence markers in draft mode**: Because draft specs bypass interactive validation, augment `[Inferred]` provenance with confidence level to help reviewers prioritize:

- `[Inferred:HIGH]` — Derived from structured source data (Rally ACs, explicit PRD requirements, numbered capability lists)
- `[Inferred:LOW]` — Extrapolated from vague context (one-line descriptions, ambiguous language, weak signals)

Other provenance markers (`[User]`, `[Rally]`, `[Codebase]`, `[Default]`) do not need confidence suffixes — their source is self-evident. This applies only to `--draft` output; in interactive mode, the conversation itself serves as the confidence filter.

**Provenance vocabulary**: Only use these exact tags in generated specs: `[User]`, `[Rally]`, `[Inferred]`, `[Default]`, `[Codebase]`. If content is adapted from a source (e.g., Rally data modified by user override), use the tag of the overriding source. Do not create compound or variant tags. Note: `[Agent Decision]` is a separate annotation category (decision attribution, not source provenance) and is not subject to this rule.

**Provenance placement**: Place tags at the **end of each paragraph, list item, or table cell** — after the content they describe, before the line break. Never place tags at section headings or at the start of paragraphs. When a paragraph has multiple sources, list all tags together at the end. Examples:

```
**Description**: The system must execute VIN validation and display metrics. **[Rally]**

- Real Bedrock API integration — uses simulated execution only **[User]**
- Must integrate with LocalStorage-based progress tracking **[Codebase]** **[Rally]**

| AC-1.1 | Fast execution | User clicks button | Deterministic side completes in <1 second **[Rally]** |
```

### Codebase Context Rules

**Do NOT read files in `spec-driven/`** — previous specifications may pollute context for the current elicitation.

**Default scan (always runs)**: Read these project-level files inline during Phase 0:
- CLAUDE.md (project-level, then global)
- README.md
- Package manifest (package.json, pom.xml, etc.)
- Top-level directory listing

This inline scan is the primary codebase context source. For large codebases (10+ top-level source directories), the SKILL.md flow may additionally delegate to a codebase scanning subagent in deep mode for source-file-level analysis. Do not read source files during inline scanning.

---

## Adaptive Flow

**Thresholds:**

- **Rich context** (Phase 0 answered all Phase 1+2 questions from subagent output, `--from` sources, or Rally): Present a formatted summary of synthesized Phase 1-2 content for **explicit user confirmation** with options: "Looks correct — proceed to requirements" / "Needs corrections" / "Let me add context."
  - **"Looks correct"**: Proceed to Phase 3.
  - **"Needs corrections"**: Ask the user which items are wrong. Update the synthesized content with their corrections, then re-present the summary for confirmation.
  - **"Let me add context"**: Accept the user's additional context as free-form input. Integrate it into the synthesized content, then re-present the summary for confirmation.
  Only proceed to Phase 3 after the user confirms. Exception: when `--draft` mode is active (explicit `--draft` flag or auto-triggered because all Phase 1+2+3 questions are covered per Draft Mode rules above), skip confirmation and generate a draft spec directly — the draft itself serves as the confirmation artifact.
- **Partial context** (most Phase 1 fields populated, some Phase 2 gaps): Ask only about gaps. Combine remaining Phase 1+2 gaps into a single exchange where possible.
- **Sparse context** (fewer than half of Phase 1 fields populated, or bare trigger like `/spec`): Standard phase flow, unchanged.

**Phase 4 pre-population**: When Phase 0 context (Rally data, `--from` input, or codebase signals) contains NFR-relevant information (performance targets, security requirements, compliance mentions, success metrics), pre-populate Phase 4 defaults from that context. Present pre-populated NFRs for confirmation ("Here are suggested NFRs based on your input — adjust or confirm") rather than asking from scratch. This extends the "never re-ask" key rule to non-functional requirements.

**Key rule**: Never ask a question whose answer is already available from Context Analysis (including inline scan results or subagent output). If the context gathering already identified the tech stack and the context-enricher extracted user types from a PRD, do not re-ask those questions.

---

## Phase Transitions

At the end of each phase, provide a brief transition summary for orientation:

```
[Phase name] complete. Captured: [2-3 bullet summary of what was established]
Next: [Phase name] — [one-line description of what we'll cover]
```

Keep these concise (3-5 lines). Adapt to what was skipped — e.g., "Phases 1-2 covered by your input. Moving to functional requirements." Their purpose is orientation, not repetition.

---

## Phase 1: Core Understanding (Required)

**Goal**: Establish the "what" and "why" in a single exchange.

**Questions to ask:**

1. **What is this feature/capability in one sentence?**

   - Free-form text input
   - Example: "Task management where teams can create and track work items"

2. **Who is this for and what problem does it solve?**

   - Free-form text input
   - Example: "Product teams who need to track feature development — currently using spreadsheets"

2b. **What's the current state?** *(Ask when not already clear from Q2)*

   - What exists today? How are users handling this now?
   - Example: "Currently using spreadsheets; no automated tracking"
   - If greenfield (nothing exists): accept "Nothing — this is new" and move on
   - If already answered in Q2 (e.g., "teams currently using spreadsheets"): skip — extract the current state from Q2's answer

3. **Why does this matter to the business?** _(Optional — skip if obvious from Q2)_

   - Can be a single sentence
   - Example: "Manual coordination costs ~2hrs/week per team"

**Slug generation**: If the user provided a feature name in the trigger (e.g., `/spec "User Authentication"`), generate the slug immediately (e.g., `user-authentication`) and confirm it inline. Do not re-ask for the feature name.

**Follow-up triggers:**

- If answer is vague ("users can do stuff"), ask: "Can you give me a specific example of what a user would do?"

**Output from this phase:**

- Feature/capability name and slug
- Overview section (including Current State)
- Primary goal

---

## Phase 2: Users and Context (Required)

**Goal**: Define who uses this and the surrounding context.

**Questions to ask:**

1. **Who are the primary users?** (multi-select)

   - End users / customers
   - Internal employees
   - Administrators
   - API consumers / developers
   - Other: [specify]

2. **Are there existing systems or features this interacts with?** _(Only ask if the feature likely integrates with other systems. Skip for clearly standalone features.)_
   - No - this is standalone
   - Yes: [list systems/APIs]
   - Not sure - needs investigation

**Follow-up triggers:**

- If "API consumers" selected, ask: "Is this a new API or extending an existing one?"
- If "Not sure - needs investigation", add as Open Question rather than blocking

**Smart defaults:**

If Context Analysis output, codebase signals, or imported context (e.g., Rally data) already identify user types or dependencies, pre-populate those values rather than asking from scratch.

**Output from this phase:**

- Users section (Primary/Secondary)
- Dependencies section

---

## Phase 3: Functional Requirements (Required)

**Goal**: Extract the core capabilities needed.

**Process:**

1. **Synthesize capabilities** from Phase 1-2 answers

   - Based on the problem description and user types, generate a list of potential capabilities
   - Present as numbered list

2. **Ask user to validate:**

   ```
   Based on your answers, here are potential capabilities:

   Must Have:
   1. [Capability 1 derived from description]
   2. [Capability 2]
   3. [Capability 3]

   Nice to Have:
   4. [Capability 4]
   5. [Capability 5]

   Reply with changes like: "drop 3, move 4 to must-have, add bulk export"
   Or just tell me what to change in your own words.
   ```

3. **User provides feedback:**

   - Moves items between categories
   - Adds missing capabilities
   - Removes irrelevant items

   **Pre-formatted AC handling**: If the user pastes acceptance criteria in Given/When/Then format (or any recognizable structured format), accept them directly:

   - Map to the appropriate FR
   - Format into the standard AC table if not already in table format
   - Mark with `[User]` provenance
   - Do not re-ask or rephrase unless there is a clear ambiguity
   - Pre-formatted ACs count toward the minimum AC threshold (see AC Quality Check below)

   This also applies during Phase 0 if ACs are present in `--from` input or Rally data.

4. **Clarify ambiguous items** (max 2 follow-ups). If edge cases emerge naturally during clarification, fold them into the relevant FR's acceptance criteria.

   ```
   "Users can share items" - do you mean:
   a) Share with specific users
   b) Share publicly via link
   c) Both
   ```

5. **Ask about exclusions and constraints:**

   ```
   Now that we know what's IN:
   - What should this explicitly NOT do?
   - Are there any hard constraints we should capture? (e.g., regulatory requirements, must integrate with existing system X, team/budget limitations)
   ```

   - Free-form text input for both
   - User can skip either or both ("nothing specific")
   - Skip the constraints question if constraints were already surfaced in Phase 1 or Phase 2 (dependencies)
   - Exclusions map to Goals > Non-Goals; hard constraints map to Scope > Constraints (non-negotiable boundaries); soft constraints and unknowns map to Scope > Assumptions

**Follow-up triggers:**

- For large scope (more than 6 must-haves), ask: "This is substantial. Should we split into multiple features/capabilities?"

**Output from this phase:**

- Functional Requirements (FR-1, FR-2, etc.)
- Each FR with:
  - Description
  - User Story format
  - Acceptance Criteria (Given/When/Then)
  - Priority (Must Have / Should Have / Nice to Have)
  - Dependencies
- In Scope (derived: summarize the validated FRs into a concise scope statement)
- Out of Scope / Non-Goals
- Constraints (hard boundaries)

**AC ID format**: IDs follow `AC-{FR-number}.{sequential}` (e.g., AC-1.1, AC-1.2). Do not use flat numbering.

**User story persona distribution**: When generating user stories for each FR, select the most relevant user type from the Users section (Phase 2). If the Users section defines multiple user types with different goals, distribute user stories across those types — don't default all stories to a single generic persona. At minimum, the two most distinct user types should each appear as the actor in at least one user story.

To select the right persona for each FR, match the FR's capability to the user type whose stated goals or pain points it most directly addresses. For example, if the Users section defines "Administrators" (goal: manage system settings) and "End Users" (goal: complete tasks efficiently), then a system configuration FR uses the Administrator persona ("As an Administrator, I want to update access policies so that permissions stay current") while a task completion FR uses the End User persona ("As an End User, I want to filter results by date range so that I see relevant items"). When an FR genuinely serves all user types equally, use the primary user type — but default to specificity over generality.

### AC Quality Check

Before proceeding to Phase 4 (or spec generation if `--minimal`), check acceptance criteria coverage:

- If any **Must Have** FR has fewer than 2 acceptance criteria, flag it:

  ```
  FR-[N] ([title]) has [count] acceptance criterion. Want to add another scenario or edge case, or is that sufficient for now?
  ```

- Accept the user's answer — if they say "that's fine," proceed and add an `[Open Question]` note to that FR in the generated spec: "Consider adding more acceptance criteria before implementation."
- One prompt per under-covered FR, then proceed. This is a quality nudge, not a gate.
- User-pasted pre-formatted ACs (from Pre-formatted AC handling above) count toward this threshold — do not re-prompt for FRs that already have user-provided ACs.

- For FRs that describe user-facing interactions involving asynchronous operations (API calls, file uploads, real-time data) or multi-panel layouts, check whether ACs cover transitional UI states: What does the user see while waiting? What appears before any data loads? What happens when a resource limit is reached? If these states are missing and the FR is Must Have, nudge: "FR-[N] involves [async operation / multi-panel UI] — should we add an AC for the loading state, empty state, or error boundary?"

### Goal-to-FR Quality Check

After all FRs are finalized (and after the AC Quality Check), verify goal coverage:

1. For each FR, assign the most relevant goal from the Goals section (Primary or Secondary-N).
   - If an FR clearly serves the Primary Goal, assign `Primary`.
   - If an FR serves a Secondary Goal, assign the specific one (e.g., `Secondary-2`).
   - If an FR doesn't clearly serve any stated goal, flag it:

     ```
     FR-[N] ([title]) doesn't clearly connect to a stated goal. Is this:
     a) Serving the primary goal (just not obviously)
     b) Serving a goal we haven't captured yet
     c) Not actually needed — should we remove it?
     ```

   - If the user declines to assign a goal ("that's fine"), set the Goal field to `TBD` and add an `[Open Question]` note: "Consider linking this FR to a specific goal before planning."

2. After assignment, check for orphan goals (goals with no supporting FRs):
   - If a Secondary Goal has no FRs, note: "Secondary Goal [N] has no supporting requirements. Want to add an FR for it, or is it already covered by existing FRs?"
   - Do not flag the Primary Goal — it should be served by the overall feature.

This is a quality nudge (like the AC Quality Check), not a gate. Accept the user's judgment.

### Risk Quality Check

After the Goal-to-FR Quality Check, review the Risks table for coverage and specificity:

- If the spec references external systems in the Dependencies section and the Risks table has zero entries, flag it:

  ```
  This feature depends on [N] external systems but has no identified risks. Want to add at least one risk related to [system availability / integration complexity / data consistency]?
  ```

- Check for risk category coverage. Well-rounded risk analysis touches at least two of these categories when applicable: technical feasibility (implementation correctness, algorithm edge cases), external dependency (availability, rate limits, API changes), and adoption/UX (user confusion, learning curve, workflow disruption). If all risks fall in a single category, nudge: "All identified risks are [category]. Are there risks in [other categories] worth capturing?"

- Watch for design decisions disguised as risks. If a risk entry describes expected system behavior or an intentional design tradeoff rather than something that could go wrong, suggest reframing: "This reads more like a design consideration than a risk. Should it move to Assumptions or Resolved Questions instead?"

This is a quality nudge (like the AC and Goal-to-FR checks), not a gate. Accept the user's judgment.

### FR Dependency Semantics

The `Dependencies` field on each FR captures **sequencing dependencies** — "this FR cannot be implemented until FR-X is complete." It does NOT capture refinement relationships (FR-3 elaborates on FR-1) or derivation (FR-3 is derived from a business rule).

If a user describes a refinement relationship ("FR-3 is basically the admin version of FR-1"), acknowledge it in the FR description but do not add it to the Dependencies field. The Dependencies field is consumed by the plan skill for task ordering — adding non-sequencing relationships would create false ordering constraints.

---

## Phase 4: NFRs and Success (Optional but Prompted)

**Goal**: Capture quality attributes and success metrics.

**Skip this phase if `--minimal` flag is provided.**

**Before suggesting defaults**: Check the project's CLAUDE.md for team-defined NFR baselines. If found, use those instead of the defaults below. The built-in table is a fallback when no project-level baselines exist.

**Feature-type NFR defaults:**

| Feature Type          | Default NFRs to Suggest                                                 |
| --------------------- | ----------------------------------------------------------------------- |
| User-facing UI        | Response time < 1s, accessibility (WCAG 2.1 AA), mobile responsive, graceful error states, offline/degraded-mode behavior, monitoring and alerting on error rates |
| API / Integration     | Latency < 200ms p95, rate limiting, idempotency, backward compatibility, retry and circuit-breaker strategy, RTO/RPO targets, API call cost budget, cost scaling with volume, health check endpoints, deployment rollback plan |
| Data processing       | Throughput targets, data validation, error recovery, audit logging, data recovery SLA, graceful degradation under load, compute cost per N records, storage cost at projected volume, job monitoring and failure alerting, runbook for manual recovery |
| Auth / Security       | Encryption at rest/transit, session management, brute-force protection, uptime target for auth service, failover strategy, authentication service monitoring, incident escalation path |
| Reporting / Analytics | Query performance, data freshness, export capabilities, report generation retry on failure, storage cost at projected volume, query cost at scale, scheduled job failure alerting, dashboard health checks |

**Questions to ask (with defaults):**

When all questions below are being asked fresh (no pre-populated answers from context), present them in a single combined exchange rather than sequential prompts. If some are already answered by context, ask only the remaining gaps.

1. **Performance requirements?**

   - Use typical defaults (API < 200ms, pages < 1s)
   - This has specific performance needs: [specify]
   - Performance isn't critical for this feature

2. **Security considerations?**

   - Standard patterns (from CLAUDE.md or codebase patterns)
   - This has elevated security needs: [specify]

3. **Reliability requirements?**

   - Standard patterns (retry, graceful degradation, error recovery)
   - This has elevated reliability needs: [specify RTO/RPO, failover, disaster recovery]
   - Reliability isn't critical for this feature

4. **Cost constraints?**

   - No specific cost targets
   - This has cost constraints: [specify budget, per-unit cost, cost scaling limits]

5. **Operability requirements?**

   - Standard patterns (logging, monitoring, alerting, health checks)
   - This has specific operability needs: [specify runbooks, deployment constraints, incident response]
   - Operability isn't a concern for this feature

6. **How will you know this is successful?** (Optional, free-form)
   - Can skip if metrics TBD
   - Example: "80% team adoption within 30 days"

**Smart defaults:**

- Pull security patterns from CLAUDE.md or codebase patterns if available
- Use standard NFR targets from config

**Output from this phase:**

- Non-Functional Requirements (NFR-1, NFR-2, etc.)
- Success Metrics section

**Open question sweep batching**: When presenting remaining open questions at the end of elicitation (see SKILL.md > Post-Elicitation Validation), batch all open questions into a single prioritized list rather than asking them one at a time. Order the list with the most impactful questions first — those that affect Must-Have FRs or block implementation decisions. The user can answer all, some, or none in a single exchange.

---

## Handling Unknowns

See the Handling Unknowns table in SKILL.md for pattern detection and responses. This section covers the detailed Agent Decision collection process.

### Agent Decision Collection

Agent decisions arise in two situations. The first is **explicit delegation**: the user says "figure it out", "you decide", "whatever works", or otherwise hands a choice to the agent. The second is **autonomous decisions**: the agent chooses between plausible alternatives during spec construction without the user explicitly delegating the choice. Common autonomous decisions include splitting a single Rally Feature into multiple FRs (a decomposition choice), elevating a quality standard beyond what the source data specified (e.g., adding WCAG AA when Rally only mentioned color contrast), adapting Rally numeric values to fit implementation reality (e.g., adjusting a timing range), or including a requirement derived purely from codebase analysis that no source mentioned. If the choice materially affects spec content and a reasonable alternative existed, it is an Agent Decision — tag and document it.

When either type of decision occurs:

1. **Announce the decision immediately in conversation** (non-blocking). Use a consistent format:
   ```
   Agent Decision: I'll [specific decision].
   Rationale: [why this choice].
   Affects: [which FRs or sections].
   Let me know if you disagree — otherwise I'll proceed with this.
   ```
   This announcement is informational, not blocking — the agent continues without waiting for explicit approval. The user can object at any point later in the conversation.

2. Record the decision in the session sidecar's `partialData.agentDecisions` array
3. Continue marking the decision inline in spec content with `[Agent Decision]` provenance
4. At spec generation time, auto-populate the `## Agent Decisions` table from the collected decisions
5. Each row should include:
   - **Decision**: What was decided (one sentence)
   - **Context**: Why a decision was needed (the question that prompted it)
   - **Rationale**: Why this particular choice (the reasoning)
   - **Affects**: Which FRs or sections are impacted (e.g., "FR-3, NFR-2")

The inline `[Agent Decision]` markers remain in the spec body for in-context visibility. The table provides a centralized review surface. If no agent decisions were made during elicitation, omit the section entirely.
