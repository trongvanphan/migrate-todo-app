# Rally Integration Guide

Optional integration with Rally via MCP tools. When Rally tools are available, the spec skill can offer to import Epic or Feature data as one of several context sources during Phase 0 Context Analysis. Rally is offered alongside — not instead of — user text, `--from` files/URLs, and codebase signals. If Rally tools are unavailable, proceed silently without Rally import.

---

## Tool Detection

Before offering Rally import, check if MCP tools exist to allow fetching Rally items by ID and listing or searching for Rally items with filters.

**Detection approach**: Attempt to use the tool. If it returns a "tool not found" error, Rally integration is not available. Do not block the workflow -- proceed silently. Rally import is one optional context source; the skill always continues without it.

---

## Object Type Inference

Before calling any Rally fetch tool, infer the correct `rallyObj` parameter from the item's ID prefix:

| ID Prefix | Rally Object Type |
| --------- | ----------------- |
| `E`       | Epic              |
| `F`       | Feature           |
| `US`      | UserStory         |
| `DE`      | Defect            |
| `DS`      | DefectSuite       |
| `TA`      | Task              |
| `TC`      | TestCase          |

Always pass the inferred type as the `rallyObj` parameter on the first call — do not rely on the tool to guess the type. If the user provides a numeric ObjectID without a prefix, ask them to clarify the item type before fetching.

---

## User Flow

Rally import is offered as part of **Phase 0: Context Analysis**, not as a separate pre-phase. When Phase 0 is gathering context sources, if Rally tools are detected, include the Rally import offer alongside other context sources being evaluated.

### Step 1: Offer Import (within Phase 0)

If Rally tools are detected, ask the user:

> "Rally integration is available. Would you like to import a Rally Epic or Feature(s) as starting context?"

Offer these options:

- **Import Rally Epic** - Fetch an Epic and its child Features
- **Import Rally Feature(s)** - Fetch specific Feature(s)
- **Skip** - Proceed without Rally data

### Step 2: Collect Item ID

If the user chooses to import:

- Ask for the Rally item ID (e.g., `E123` for Epic, `F456` for Feature)
- For Epics: also offer to fetch child Features, filtered by the Epic

### Step 3: Fetch and Map

Fetch the item from Rally using the `rallyObj` type inferred from the ID prefix (see Object Type Inference above). For Epics, fetch all child Features and their child Stories.

**Fetch resilience**: If a Rally fetch does not return within 15 seconds, retry once. If the second attempt also fails or times out, emit a status update ("Rally data unavailable — proceeding without it") and continue Phase 0 with other context sources. Maximum 2 attempts per item. On each retry, emit progress so the user knows the skill is not stuck: `"Retrying Rally fetch for [ID]..."`

---

## Rally Field-to-Spec Mappings

### Epic Import

| Rally Field                           | Spec Section                    | Notes                                |
| ------------------------------------- | ------------------------------- | ------------------------------------ |
| `Name`                                | Spec name / Overview title      | Used as starting point for spec slug |
| `Description`                         | Overview                        | Extract the "what" and "why"         |
| `Notes`                               | Additional context for Overview | Supplementary detail; also scan for scope boundary language (see below) |
| `State`                               | Priority hint                   | See state-to-priority mapping table below |
| `UserBusinessValue`                   | Goals (Primary)                 | Maps to value proposition            |
| `Description` (Success Metrics block) | Success Metrics (Primary + Secondary) | Extract metric definitions from Description text. If Epic-level metrics are not applicable at Feature scope, document the omission as an Agent Decision |
| Child Features                        | Functional Requirements (seeds) | Each Feature becomes a candidate FR  |

### Feature Import

| Rally Field                           | Spec Section              | Notes                                         |
| ------------------------------------- | ------------------------- | --------------------------------------------- |
| `Name`                                | FR title                  | Direct mapping                                |
| `Description`                         | FR description            | Extract capability details                    |
| `Notes`                               | FR additional context     | Supplementary detail; also scan for scope boundary language (see below) |
| `State`                               | Priority hint             | See state-to-priority mapping table below     |
| Child Stories                         | Acceptance criteria       | Fetch Name + Description + AcceptanceCriteria for each Story (see Story Import below) |

### Story Import

When fetching child Stories under a Feature, retrieve the following fields for each Story:

| Rally Field           | Spec Section                | Notes                                                         |
| --------------------- | --------------------------- | ------------------------------------------------------------- |
| `Name`                | FR acceptance criterion label | Story name describes a specific behavior                    |
| `Description`         | FR description detail       | Story description becomes the FR description or supplements it |
| `AcceptanceCriteria`  | FR acceptance criteria      | Map directly to Given/When/Then format if present; preserve verbatim otherwise |

Present full extracted Story detail — not just titles — so acceptance criteria are available for the spec from the start.

---

## Rally State-to-Priority Mapping

Use Rally item state as a suggested priority for the spec. Always present this as a default the user can override.

| Rally State                  | Suggested Priority | Rationale                              |
| ---------------------------- | ------------------ | -------------------------------------- |
| Discovering / Defining       | Nice to Have       | Still being shaped; not yet committed  |
| Ready / Groomed              | Should Have        | Validated but not actively in progress |
| In-Progress / Dev Complete   | Must Have          | Active work with high commitment       |
| Accepted / Released          | Must Have          | Already delivered or formally committed |

**Instruction**: Use this table as the default suggestion when pre-populating priority fields. Always let the user override — the state reflects Rally workflow status, not necessarily product priority.

---

## Scope Boundary Language Detection

When processing `Description` and `Notes` fields from any Rally item (Epic, Feature, or Story), scan for exclusion language and extract candidate Non-Goals:

**Trigger phrases**: "will not", "won't", "out of scope", "not included", "not in scope", "future", "deferred", "excluded", "does not include"

**Extraction rule**: If a sentence or bullet contains one of these phrases, extract it as a candidate Non-Goal for Phase 3's exclusion step.

**Example**:
> Notes: "This feature will not support bulk import. Mobile support is deferred to a future release."

Extracted Non-Goal candidates:
- "will not support bulk import"
- "Mobile support is deferred to a future release"

Present these candidates during Phase 3 when defining explicit exclusions, so the user can confirm, edit, or discard them.

---

## Pre-Population Strategy

After fetching Rally data:

1. **Tracking field**: Populate the spec template's `Tracking:` header with the Rally item ID and link (e.g., `E123` or `F456`). If multiple items are imported, list all IDs.

2. **Phase 0 gap analysis**: Feed all extracted Rally data into the Context Analysis gap analysis. Include Epic/Feature names, descriptions, acceptance criteria, and any extracted Non-Goal candidates. Present what was found and what still needs elicitation.

3. **Phase 1 (Core Understanding)**: Pre-fill the "one sentence description" from Epic/Feature Name + Description. Present to user for confirmation/refinement rather than skipping the phase entirely.

4. **Phase 2 (Users and Context)**: If child Features exist, suggest them as scope items. Present as a starting list the user can modify.

5. **Phase 3 (Functional Requirements)**: Seed the capabilities list from child Features or Stories (with full descriptions and acceptance criteria). Seed the Non-Goals list from any scope boundary language extracted from Notes/Description. The user still validates, adds, and removes items.

6. **Phase 4 (NFRs)**: Rally data rarely contains NFR information. Proceed with standard elicitation.

**Important**: Rally data is a starting point, not a substitute for elicitation. Always present imported data for user confirmation and continue the interactive process.

**Epic-to-Feature metric scoping**: When importing from an Epic, some Epic-level success metrics may not apply to the Feature being specified (e.g., cross-team behavioral metrics). Import Feature-level metrics directly. For Epic-level metrics NOT imported, record an Agent Decision: "Excluded Epic metric [X] — not measurable at Feature scope."

**Terminology preservation**: When importing content from Rally or other external sources, preserve the original terminology (e.g., "exercise", "module", "sprint"). Do not silently substitute synonyms. If terminology must change to fit the spec context, document the change in the Agent Decisions section with rationale.

**Rally data drift detection**: Never silently modify Rally numeric values, quantities, or constraints — either preserve them exactly with `[Rally]` provenance, or document the adaptation as an `[Agent Decision]`.

When adapting, restructuring, or reinterpreting Rally-imported values during spec generation — splitting a Rally Feature description into multiple FRs, adjusting numeric thresholds, changing quantity constraints (e.g., "six" to "at least six"), or reframing acceptance criteria — tag the adapted content with `[Agent Decision]` and document the specific change and rationale. For example, if a Rally Feature description is split into FR-2 and FR-3 for distinct acceptance scopes, both FRs should carry an Agent Decision entry: "Split Rally Feature F-123 into FR-2 (orchestration) and FR-3 (validation) for independent testability."

---

## Error Handling

| Error              | Detection                                       | Response                                                                      |
| ------------------ | ----------------------------------------------- | ----------------------------------------------------------------------------- |
| Tool not available | MCP tool call returns "tool not found"          | Skip Rally integration silently. Continue Phase 0 with other context sources. |
| Item not found     | Tool returns empty result or "not found" error  | Inform user: "Could not find Rally item [ID]. Proceeding without Rally data." |
| Network/auth error | Tool returns connection or authentication error | Inform user: "Unable to connect to Rally. Proceeding without Rally data."     |
| Invalid ID format  | User provides unrecognized format               | Ask user to provide a valid Rally ID (e.g., E123, F456) or skip.              |

In all error cases, the spec elicitation workflow continues normally without Rally data. Rally import is an enhancement, never a blocker.
