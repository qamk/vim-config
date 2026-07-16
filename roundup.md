# Roundup Reports

**Purpose**: Summarise issues investigated or resolved over a date range, drawing from problem-solution reports, analysis reports, and investigation notes. Provides a scannable overview of what happened, what the impact was, and where things stand.

**When to Use**:
- Periodic issue summaries (weekly, fortnightly, monthly)
- Stakeholder briefings on support and engineering work
- Identifying recurring themes across multiple issues
- Sprint or cycle retrospectives

**When NOT to Use**:
- Fewer than 2 issues in the date range (use individual reports instead)
- Deep-dive into a single issue (use problem-solution or analysis)
- Feature documentation (use feature-release or outline)

**Variants**: Single (no audience split). Technical language is acceptable but must be scannable — a reader should be able to parse any technical detail in a single pass without needing to look anything up. Stakeholders who need deeper detail follow the ticket references to the underlying reports.

---

## Filename Convention

**Pattern**: `roundup_<start_YYYY_MM_DD>_to_<end_YYYY_MM_DD>[_<modifier>].md`

**Examples**:
- `roundup_2026_04_14_to_2026_04_27.md`
- `roundup_2026_04_01_to_2026_04_30_by_theme.md`
- `roundup_2026_04_14_to_2026_04_27_condensed.md`

**Storage**: `$REPORTS_DIR/roundup_reports/` (flat directory, no subdirectories).

---

## Content Constraints

- **No code blocks.** No inline code references to file paths, function names, or line numbers.
- **No diagrams.** No mermaid, ASCII, or other visual elements. The `--with-diagram` flag is not applicable.
- **Architecture references**: When referring to services or system components, cite the project architecture doc rather than describing internals inline. Use plain-language service names (e.g., "the document-processing service") rather than deployment names or namespaces.
- **Ticket references**: Include clickable links to issue trackers. These are the primary mechanism for readers to access deeper detail.
- **Tables**: Used for the Status Summary Table and per-entry metadata tables. Individual issue entries use prose for narrative content, with a metadata table immediately below each entry heading.

---

## Collapsible Sections

Sections listed here should be wrapped in `<details>`/`<summary>` at authoring time. `/publish` handles per-adapter conversion.

| Variant | Collapsible Sections | Rationale |
|---------|---------------------|-----------|
| (single) | Each individual issue entry | Status summary table is the scan path; entries are expand-on-demand detail |

The `<summary>` for each issue entry should be the entry heading (e.g., "1. Oversized Analysis Output Broke Customer Threads — Shipped"). The status label in the summary lets readers decide whether to expand without opening.

## Report Structure

### 1. Report Header

```markdown
# Issues Roundup: <start_date> to <end_date>

**N issues** investigated or resolved. [One sentence identifying the dominant theme if one exists.]
```

The header states the date range, total issue count, and optionally a single-sentence thesis about the period's dominant pattern. Keep it to 2-3 lines.

### 2. Status Summary Table

Always present. One row per issue. This is the "at a glance" entry point — a reader who only scans this table should understand the landscape.

**Columns**:

| Column | Content | Guidance |
|--------|---------|----------|
| **#** | Sequential number | Matches the numbered entry in section 3. Preserved across grouping modifiers. |
| **Week** | Continuity indicator | `New` for first appearance. `Week N` for carried-over issues (N = consecutive roundup count including this one). Derived from prior roundup comparison during curation. |
| **Ticket** | Clickable ticket ref or "---" | Link to issue tracker. Multiple tickets for one issue: list the primary. |
| **Issue** | One-line summary | Max ~60 characters. Describe the symptom, not the cause. |
| **Status** | Status label | Read from source report `status` field, or assigned during curation for note-only issues. See status vocabulary below. |
| **Impact** | One-line impact | Who was affected and how. Quantify where possible. |
| **Resolution** | One-line resolution or next step | What was done, or what is planned. |

**Status vocabulary**:

The roundup uses a unified status vocabulary. For issues backed by a report, the status is read from the report's `status` frontmatter field. For note-only issues, the status is assigned during the curation step (see "Curation Workflow" below).

Report-level statuses (stored in report frontmatter):
- **Shipped** — resolution deployed to production and considered complete — color: `green`
- **Communicated** — investigation complete, findings and recommendations delivered; awaiting external decision — color: `green`
- **Revisiting** — resolution explored but approach being reconsidered — color: `orange`
- **Monitoring** — resolution deployed, watching for recurrence or verifying effectiveness — color: `orange`

Roundup-only statuses (assigned during curation for note-only issues, not stored in any frontmatter):
- **Planned** — resolution designed, not yet implemented — color: `yellow`
- **Underway** — resolution actively being implemented; some improvements delivered, more in progress — color: `blue`
- **Investigating** — active investigation, no resolution yet — color: `blue`
- **Hypothesis** — theory documented, not yet verified against evidence — color: `purple`
- **Blocked** — progress stalled on a dependency or decision — color: `red`
- **Deprioritised** — investigation concluded, fix deferred indefinitely due to low impact or reproduction difficulty — color: `gray`

**Status legend**: immediately after the status summary table, include a collapsible block defining each status label. This ensures readers of the published report can understand the vocabulary without looking anything up.

```markdown
<details>
<summary>Status definitions</summary>

- **Shipped** — resolution deployed to production and considered complete
- **Communicated** — investigation complete, findings and recommendations delivered; awaiting external decision
- **Revisiting** — resolution explored but approach being reconsidered
- **Monitoring** — resolution deployed, watching for recurrence or verifying effectiveness
- **Planned** — resolution designed, not yet implemented
- **Underway** — resolution actively being implemented; some improvements delivered, more in progress
- **Investigating** — active investigation, no resolution yet
- **Hypothesis** — theory documented, not yet verified against evidence
- **Blocked** — progress stalled on a dependency or decision
- **Deprioritised** — investigation concluded, fix deferred indefinitely due to low impact or reproduction difficulty

</details>
```

**Example**:

```markdown
| # | Week | Ticket | Issue | Status | Impact | Resolution |
|---|------|--------|-------|--------|--------|------------|
| 1 | New | [GH #2916](url) | Oversized analysis output broke threads | Shipped | 2 customers, threads permanently broken | 50k-char output cap + auto-recovery |
| 2 | Week 2 | [Pylon #340](url) | Document-parser overload incident | Planned | 10 customers, 40+ threads, 90-min window | Tiered remediation: ack deadlines, HPA, bulkheads |
| 3 | New | --- | Thread duplication with attachments | Hypothesis | Unknown scope | Code-reading analysis, not yet verified |
```

### 3. Issue Entries

Default ordering: chronological by the date the issue was first reported or investigated. Numbered list matching the Status Summary Table.

Each entry is a subsection (`### N. Issue Title`) with a **per-entry metadata table** immediately below the heading, followed by prose covering the content pillars.

#### Per-Entry Metadata Table

A single-row table placed between the entry heading and the prose body. Uses the same columns as the Status Summary Table, scoped to this one issue. This colocates structured data with the narrative so readers don't have to scroll back to the summary table.

```markdown
### 3. Silent File-Attach Failure via Document-Parser Timeout

| # | Week | Ticket | Issue | Status | Impact | Resolution |
|---|------|--------|-------|--------|--------|------------|
| 3 | Week 2 | [Pylon #321](url) | Skill-generated files silently failed to attach | Planned | Silent failure; files written but invisible to users | Observability fix, async reconciliation |

[prose follows]
```

#### Content Pillars

**What happened** (1-3 sentences)
- Describe the problem in terms of user-visible behaviour or system symptoms.
- No root-cause detail here — just what went wrong.

**What was the impact** (1-2 sentences)
- Customer, user, or business impact in concrete terms.
- Quantify where possible: number of customers, sessions, threads, duration, revenue.

**Who / how many were affected** (1 sentence)
- Name customers if known and appropriate. State user counts, team scope, or service scope.
- If cross-tenant: say so explicitly.

**Resolution or next steps** (1-3 sentences)
- If shipped: what was done, in plain language. Reference the PR or ticket for detail.
- If planned: what is the plan and rough timeline.
- If investigating/hypothesis: what is known and what remains.

**Status** (included in the entry heading or as a label)
- Use the same vocabulary as the Status Summary Table.

#### Entry Example

```markdown
### 1. Oversized Analysis Output Broke Customer Threads

| # | Week | Ticket | Issue | Status | Impact | Resolution |
|---|------|--------|-------|--------|--------|------------|
| 1 | New | [GH #2916](url) | Oversized analysis output broke threads | Shipped | 2 customers, threads permanently broken | 50k-char output cap + auto-recovery |

Ellie's analysis tool sometimes produced enormous output that exceeded model context limits. The oversized result broke the thread and got cached, making it permanently unrecoverable on reload.

Two customers (ES, LSH) had threads that could not be opened. No data outside the broken analysis step was affected.

A 50k-character cap on tool output was shipped (PR #3032), along with guidance for handling large data, broken-state cache prevention, and auto-recovery for already-broken threads.
```

#### Length Guidance

- **Per entry**: 4-8 sentences total across all pillars. Err toward brevity.
- **Overall**: A 7-issue roundup should be 2-3 pages including the table and themes section. Scale linearly — 15 issues might be 4-5 pages.

### 4. Recurring Themes

Bottom section. Identifies 2-5 cross-issue patterns. This is synthesis, not repetition — do not restate issue details.

**For each theme**:
- The pattern observed (1-2 sentences)
- Which issues it connects (by number, cross-referencing the status table)
- Whether the pattern is being addressed systemically or only per-incident (1 sentence)

**Example**:

```markdown
## Recurring Themes

**Document-parser reliability** — Issues #2, #3, #4, and #7 all involve the shared document-processing service. The shared-tenancy, no-isolation architecture is the systemic root. Tier 1 (ack deadline config) is shipping this sprint; tenant bulkheads are scoped but not yet committed.

**Deployment interruptions** — Issues #4 and the older Pylon #184 share the same pattern: routine deployments killing in-flight work. Graceful shutdown is planned as the fix.
```

If fewer than 2 themes emerge, state that explicitly: "No recurring cross-issue themes were identified in this period."

---

## Grouping Modifier Behaviour

Grouping modifiers change **only section 3 (Issue Entries)**. Sections 1 (header), 2 (status summary table), and 4 (recurring themes) remain unchanged.

Issue numbers from the status summary table are **always preserved** regardless of grouping — they are never renumbered within groups. This keeps cross-referencing consistent.

### Choosing a grouping: default vs. heavy weeks

The default presentation is **flat** — a single numbered issue list matching the status summary table. This is the right choice for a typical week.

Switch to **`by-theme`** when the period is **heavy**, i.e. a flat list stops being scannable. A week is heavy when either condition holds:

- **Volume** — the issue count is roughly **10 or more** (typical weeks run ~5–9).
- **Spread** — the issues span **4 or more distinct subsystems/themes**, so a flat list forces the reader to mentally re-cluster.

When **both** hold, `by-theme` is strongly preferred: theme headings give the reader a scannable map while the status summary table stays the single flat index. For lighter weeks, keep the flat default even if a few themes exist — the overhead of theme sections is not worth it below the volume threshold.

This is a guideline, not a hard gate. The author may still pick flat for a heavy-but-thematically-uniform week, or `by-theme` for a smaller week dominated by one sprawling theme. When the heavy thresholds are met, the `/report` skill should surface the `by-theme` option to the user (with the issue count and theme spread that triggered it) rather than silently defaulting to flat.

### `by-theme`

Issues regrouped under theme headings derived from the Recurring Themes analysis. Each issue appears under exactly one theme. Issues that don't fit a theme go under "Other".

```
## Issues by Theme

### Document-Parser Reliability
#### 2. Document-Parser Overload Incident (Pylon #340)
[5 pillars]
#### 3. Silent File-Attach Failure (Pylon #321)
[5 pillars]

### Deployment Resilience
#### 4. Ellie Slow Response — Deploy Interrupted Work (Pylon #337)
[5 pillars]

### Other
#### 1. Oversized Analysis Output (GH #2916)
[5 pillars]
```

When `by-theme` is active, the Recurring Themes section at the bottom is shortened to cross-cutting observations only (patterns that span multiple theme groups).

### `by-status`

Issues regrouped under status headings. Status order: Shipped > Planned > Investigating > Hypothesis > Monitoring > Blocked.

```
## Issues by Status

### Shipped
#### 1. Oversized Analysis Output (GH #2916)
[5 pillars]

### Planned
#### 4. Ellie Slow Response (Pylon #337)
[5 pillars]

### Hypothesis
#### 7. Thread Duplication with Attachments
[5 pillars]
```

### `by-scope`

Issues regrouped under affected service/area headings. Scope labels are inferred from the source material. Use plain-language service names. Issues that can't be cleanly categorised go under "Other".

```
## Issues by Scope

### Document Processing
#### 2. Document-Parser Overload Incident (Pylon #340)
[5 pillars]

### Ellie Core
#### 1. Oversized Analysis Output (GH #2916)
[5 pillars]

### Other
...
```

### Mutual Exclusivity

Only one grouping modifier may be active at a time. `by-theme`, `by-status`, and `by-scope` conflict with each other. The `/report` skill rejects combinations with: "Grouping modifiers (by-theme, by-status, by-scope) are mutually exclusive."

---

## Source Material

The roundup draws from artefacts found via `/lookup` within the specified date range:

- **Problem-solution reports** — for resolved issues (shipped fixes, customer impact, resolution detail)
- **Analysis reports** — for investigated issues (root cause analysis, recommendations)
- **Investigation notes** — for in-progress or hypothesis-stage issues (evidence gathered, hypotheses formed)
- **Handoff reports** — for escalated issues (what was tried, why escalated)

The report-builder reads these sources to extract the five content pillars per issue. It should **not invent issues** that are not present in the source material, and should **not repeat full investigation detail** — the roundup is a summary layer that links out to the detailed artefacts.

When source material for an issue includes both notes and a formal report, prefer the report as the primary source (it has already been through editorial review).

---

## Carry-Over Policy

A prior-roundup issue is only included in the current roundup if at least one of the following is true:

1. **Non-terminal status** — the issue's status is one that implies outstanding work: `Planned`, `Investigating`, `Revisiting`, `Hypothesis`, `Blocked`.
2. **Status changed since the prior roundup** — e.g. `Planned` → `Shipped`. The issue appears one final time to report the resolution, then drops off.
3. **Explicitly requested** — the user asks for it to be included during curation.

**Terminal statuses** — these do NOT carry forward unless criterion 2 or 3 applies:
- **Shipped** — work is done.
- **Communicated** — ball is in someone else's court; no action on our side.
- **Monitoring** — system recovered or fix deployed; watching passively.
- **Deprioritised** — investigation concluded, fix deliberately deferred.

If a monitoring/communicated/shipped item resurfaces (new incident, customer reply, regression), it re-enters as a **carried-over** item. The `Week N` count reflects total roundup appearances (not consecutive), so the builder must determine the correct count by following the artifact graph: the resurfacing source material's `related`/`tickets` fields link back to older artifacts, which appear in prior roundups' frontmatter. Match the ticket across those prior roundups to count appearances. This avoids an exhaustive search of all historical roundups — the links are already in the index.

---

## Curation Workflow

Before generating the roundup body, the report-builder presents the candidate artefact set to the user for review. This step serves as a status reconciliation checkpoint — the natural moment to update report statuses and adjust scope.

### Step 1: Present candidates

List all artefacts found within the date range, grouped by issue. For each issue show:
- Ticket reference(s)
- Source artefact type (report or note) and path
- Current status (read from report `status` frontmatter, or "unassigned" for note-only issues)

### Step 2: Prompt for status updates

For each issue, ask the user to confirm or update the status:

- **Report-backed issues**: show the current `status` from frontmatter. If the user changes it, update the source report's frontmatter before generating the roundup.
- **Note-only issues**: no status exists yet. Ask the user to assign one from the full roundup vocabulary (`shipped`, `revisiting`, `monitoring`, `planned`, `investigating`, `hypothesis`, `blocked`). This status is used in the roundup only — it is not written back to the note.

### Step 3: Include / exclude artefacts

Ask the user:
- Whether to **exclude** any candidates (e.g. not worth covering, already covered in a previous roundup)
- Whether to **include** additional artefacts from outside the date window (e.g. a note from the prior week that is now relevant, or a report that was updated after its original date)

### Step 4: Proceed to generation

Once the user confirms the curated set and statuses, generate the roundup body using the confirmed data.

---

## Frontmatter

```yaml
---
type: report
subtype: roundup
date: <generation_date>
date_range:
  since: <start_date>
  until: <end_date>
tags: [roundup, ...]
tickets:
  - <all ticket refs included in the roundup>
related:
  - path: <source report or note path>
    relationship: source
---
```

---

## Modifiers Reference

See `agentic://reports/modifiers.md` for:
- `by-theme`, `by-status`, `by-scope` — grouping modifiers (roundup-specific)
- `condensed` — compress entries to status + 1-2 bullets each

---

## Index Fields

Artefact-specific columns added to the publishing index when a roundup report is published. These supplement the mandatory index fields defined in `/publish` step 7.

```yaml
index_fields:
  - name: Date Range
    type: text
    source: frontmatter.date_range
    description: "Period covered by the roundup (since — until)"
  - name: Issue Count
    type: number
    source: body
    description: "Number of issues covered in the roundup"
```
