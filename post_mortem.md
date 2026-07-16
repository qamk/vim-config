# Post-Mortem Reports

**Purpose**: Document production incidents end-to-end — what happened, who was affected, how it was resolved, and what we learn from it. Serves as both a record of the event and a catalyst for systemic improvement.

**When to Use**:
- Production outages or degraded service affecting customers
- Regressions introduced by deployments
- Data integrity incidents
- Security incidents
- Near-misses that warrant documentation for prevention

**Note:** Post-mortem reports are retrospective — written after the incident is resolved or mitigated, not during active response. If the incident is still active, focus on resolution first; the report captures the full picture afterwards. Investigation notes (`$NOTES_DIR/`) are the working memory during the incident; this report distils them into a formal record.

**Filename Convention**: `postmortem_<YYYY_MM_DD>_<brief_description>.md`
Examples:
- `postmortem_2026_05_08_fabric_permission_denied.md`
- `postmortem_2026_04_22_payment_sync_outage.md`

## Formatting Guidelines

### Visual Elements for Clarity

**Tables** — inline, no opt-in needed. Use for affected customers, timeline events, or blast radius:
| Customer | Impact | Duration | Confirmed |
|----------|--------|----------|-----------|
| BXP | Fabric queries blocked | ~47 min | Yes |
| MadisonInt | Potentially affected | Unknown | No |

**ASCII diagrams** — inline, no opt-in needed. Use for causal chains:
```
Deploy (skills-rbac) → RBAC grants populated → empty-grants bypass disabled
                                                         ↓
                                              Fabric queries denied (403)
```

**Inline mermaid diagrams** — opt-in via `/report --with-diagram`. Same authoring rules as problem-solution reports (see `agentic://reports/problem_solution.md` "Visual Elements for Clarity"). Timelines and sequence diagrams are the most common shapes for incident reports.

**Audience-aware complexity.** Incident reports serve a mixed audience. Default to the operational/leadership budget (~5 nodes). If the post-mortem section needs deeper technical detail, a second technical diagram is acceptable (~8-10 nodes).

## Collapsible Sections

| Collapsible Sections | Rationale |
|---------------------|-----------|
| Detailed Timeline | The summary and resolution are the scan path; full timeline is reference |
| Post-Mortem: Technical Detail | High-level lessons are load-bearing; deep-dive is supplementary |

## Required Metadata

The report-builder must prompt for the following if not provided in context:

1. **People involved** — who responded to the incident (names and roles)
2. **Severity** — one of the severity tiers below
3. **Detection method** — one of the detection methods below

If the user's context (conversation, notes, ticket) already contains this information, extract it rather than prompting.

## Severity Tiers

**REQUIRED** in frontmatter as `severity`. Enum: `P0` | `P1` | `P2` | `P3` | `P4`.

Severity is assigned based on the **worst confirmed impact** at the time of the incident, not the final outcome after resolution. If severity is unclear, the report skill prompts the user with these definitions.

| Tier | Label | Criteria | Examples |
|------|-------|----------|----------|
| **P0** | Outage | Complete platform outage or total loss of service for all customers; widespread data loss or corruption | Platform down, all customers unable to access the product, catastrophic data loss |
| **P1** | Critical | Complete loss of a core capability for one or more customers; targeted data loss or corruption; security breach | Payment processing down for a customer, data leaked, login completely broken |
| **P2** | High | Significant degradation of a core capability; workaround exists but is burdensome; multiple customers affected | Key reports inaccessible, sync delays >1 hour, login failures for a subset of users |
| **P3** | Medium | Partial degradation of a non-core capability; single customer affected; workaround is straightforward | One customer's Fabric queries blocked, a single report type failing, cosmetic data error |
| **P4** | Low | Minor issue with negligible customer impact; near-miss caught before customer exposure | Internal tooling error, staging-only regression, config drift detected before deploy |

**Severity legend**: include a collapsible block in the rendered report immediately after the Incident Summary, so readers can reference the tier definitions without looking them up:

```markdown
<details>
<summary>Severity definitions</summary>

- **P0 — Outage**: Complete platform outage or total loss of service for all customers; widespread data loss or corruption
- **P1 — Critical**: Complete loss of a core capability for one or more customers; targeted data loss or corruption; security breach
- **P2 — High**: Significant degradation of a core capability; workaround exists but is burdensome; multiple customers affected
- **P3 — Medium**: Partial degradation of a non-core capability; single customer affected; straightforward workaround
- **P4 — Low**: Minor issue with negligible customer impact; near-miss caught before customer exposure

</details>
```

## Detection Methods

**REQUIRED** in frontmatter as `detection_method`. Describes the **initial detection** — how the incident first came to our attention. Subsequent communication (e.g. customers reporting after we already knew) belongs in the report body's timeline, not this field.

Enum: `error_tracking` | `alert` | `customer_report` | `internal_discovery` | `audit`.

| Method | Description | Reactive/Proactive |
|--------|-------------|-------------------|
| **error_tracking** | Discovered via application error signals — exceptions in observability software, error-level log entries, failed health checks. Something already broke and we noticed. | Reactive |
| **alert** | Threshold-based alerting fired before or alongside customer impact. A metric or SLO crossed a boundary. | Proactive |
| **customer_report** | Customer or end-user reported the issue before we detected it internally. | Reactive |
| **internal_discovery** | Discovered internally during development, code review, or manual testing — not via automated signals. | Proactive |
| **audit** | Surfaced by a structured review — security audit, dependency scan, compliance check, or scheduled evaluation against live systems. | Proactive |

## Status Field

**REQUIRED** in frontmatter as `status`. Enum: `resolved` | `mitigated` | `monitoring`.

- **resolved** — root cause addressed, fix deployed, incident closed
- **mitigated** — workaround or partial fix in place, root cause fix pending
- **monitoring** — fix deployed, watching for recurrence before closing

## Structure

### 1. Incident Summary (3-5 sentences)

- What service or capability was affected
- Customer impact in plain language
- Duration (first detected → resolved/mitigated)
- Current status

### 2. Key Timestamps

Sidebar-style metadata block immediately after the summary. Gives readers the critical timing at a glance without reading the full timeline.

| Field | Description |
|-------|-------------|
| **Reported** | When the incident was first reported or detected |
| **Impact start** | When customer impact began (may differ from detection) |
| **Fixed** | When the fix was deployed to production |
| **Closed** | When the incident was declared resolved |
| **Duration** | Total time from impact start to fixed |

### 3. People Involved

| Name | Role | Involvement |
|------|------|-------------|
| ... | ... | Detected / Investigated / Fixed / Reviewed / ... |

### 4. Timeline

Chronological record of key events. Use UTC with local-time parenthetical where relevant.

**Format**: Bulleted list with timestamps. Include:
- When the incident was introduced (deploy, migration, config change)
- When it was first detected
- When investigation started
- Key milestones during investigation
- When the fix was identified, deployed, and verified

Wrap the detailed timeline in `<details>` if it exceeds ~8 entries; keep a 3-4 line summary visible.

### 5. Who Was Affected

- Which customers, how many users
- What capabilities were degraded or unavailable
- Confirmed vs. potentially affected (distinguish clearly)
- Business impact if quantifiable (blocked workflows, revenue at risk)

### 6. Narrative

Non-technical narrative of the incident suitable for a mixed audience. Explain the causal chain — what changed, why it broke things, and why it wasn't caught beforehand. Avoid file paths and code; focus on system-level behaviour.

For technical readers who want depth, reference the Post-Mortem section.

### 7. Resolution

- What fix was applied (describe at system level, not code level)
- PR or deploy reference (link)
- Who authored and reviewed the fix
- When the fix was deployed
- How resolution was verified

### 8. Post-Mortem

#### Root Cause

Technical explanation of the root cause. Include file paths, code references, and the specific mechanism. This section can assume engineering familiarity.

#### Contributing Factors

What conditions enabled the incident beyond the immediate trigger:
- Missing tests or validation
- Architectural assumptions that proved fragile
- Process gaps (review, deploy, monitoring)

#### Learnings and Risks

What we learned from this incident — both positive and negative. Each entry is a summary/detail pair capturing knowledge gained, whether it's something that worked well, something that needs to change, or a risk this incident exposed.

Positive learnings (what worked):
- Fast detection, effective collaboration, good tooling, etc.

Negative learnings (what needs to change):
- Detection gaps, communication gaps, process gaps, architectural weaknesses

Risks uncovered:
- Fragilities, assumptions, or patterns that could cause similar or worse incidents

### 9. Next Steps

Concrete, actionable follow-ups. Each item should have an owner (name or team) and a target timeframe where possible.

| Action | Owner | Target | Status |
|--------|-------|--------|--------|
| ... | ... | ... | Pending / In Progress / Done |

Distinguish between:
- **Immediate** — required to fully close the incident
- **Short-term** — prevent recurrence of this specific incident
- **Long-term** — address systemic contributing factors

## Modifiers

No modifiers defined for this report type yet.

## Common Mistakes

- Treating the report as blame assignment rather than systemic learning
- Writing the timeline from memory instead of from logs/Sentry/git timestamps
- Omitting positive learnings — incident reports that are purely negative discourage future transparency
- Mixing technical depth into "What Happened" (save it for Post-Mortem)
- Vague next steps without owners or timeframes ("we should improve testing")
- Not distinguishing confirmed vs. potential impact in the blast radius
- Writing the report during active incident response instead of after resolution

## Success Criteria

An incident report succeeds when:
- A new team member can understand what happened without asking follow-up questions
- Leadership can assess business impact and resource needs from the summary alone
- Engineering can reproduce the investigation path from the timeline and post-mortem
- Next steps are concrete enough to be tracked as tasks
- The post-mortem identifies systemic improvements, not just the immediate fix
