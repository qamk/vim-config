# Unified Artefact Frontmatter Schema

Single frontmatter contract shared by notes, reports, playbooks, and ground-audits. All Claude skills that read/write these artefacts (`/note`, `/report`, `/playbook`, `/ground`, `/lookup`, `/investigate`, `/publish`) conform to this schema.

## Design principles

- **One schema, multiple artefact types.** Fields are added or omitted based on artefact type; the validation rules know which fields are required where.
- **Taxonomy separation.** Raw values live in frontmatter. Vocabulary semantics (aliases, implies, enum members) live in the project's `taxonomy.json`. Index builder and validator apply taxonomy at build/query time.
- **Rename-and-extend, not replace.** Existing fields (`category`, `tags`, `related_notes`) get renamed to unified equivalents; their semantics are preserved. Existing validator/export tooling migrates, it doesn't get discarded.
- **IDs computed, not stored.** Filename minus extension minus date prefix is the ID. Eliminates drift.

## Fields

### Core (all artefact types)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | enum | yes | `note` \| `report` \| `playbook` \| `ground-audit` |
| `date` | ISO date `YYYY-MM-DD` | yes | Creation date. Index uses this for chronology and DAG invariant. |
| `subtype` | string (taxonomy-validated) | yes | Specific flavour within the type. See subtype section below. |
| `tags` | `[string]` (taxonomy-validated) | no | Topical tags. Free list; normalised via taxonomy aliases; expanded via `implies`. |
| `scope` | `[string]` | no | Component path(s) the artefact concerns. Free-form path strings like `messaging-service/queue`; validated against project `architecture.md` known_components if present (warn-only). |
| `tickets` | `[string]` | no | External ticket references, each in `<source>:<id>` form: `gh:owner/repo#123`, `jira:PROJ-1234`, `linear:ENG-456`. |
| `part` | string | no | Present on split artefacts. Format: `"N of M"`. Encodes this file's position within a multi-part set. |
| `focus` | string | no | Present on split artefacts alongside `part`. Short label (≤10 words) describing the semantic focus of this part, derived from its top-level headings. |
| `related` | `[{path, relationship}]` | no | Structured links to other artefacts. Same shape as existing `related_notes`. Path relative to `$PROJECT_ROOT`. Relationships: `similar-pattern`, `context-for`, `follows-up`, `extracted-from`, `supersedes`. Validator enforces DAG invariant for same-type links. |

### Reports and playbooks

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | enum | yes (reports, except roundup) | Resolution lifecycle. Enum: `shipped` \| `communicated` \| `revisiting` \| `monitoring`. Default: `shipped`. **shipped**: resolution deployed to production and considered complete. **communicated**: investigation complete, findings and recommendations delivered; awaiting external decision. **revisiting**: resolution explored but approach being reconsidered (rejected during review, not fit-for-purpose, or superseded by broader design). **monitoring**: resolution deployed, watching for recurrence or verifying effectiveness. Roundup reports use a broader vocabulary in body tables for note-only issues — see roundup doc. |
| `audience` | `[enum]` | yes (reports, playbooks) | Who the artefact targets. Members: `operational`, `technical`, `engineering`, `leadership`, `on-call`, `support-engineer`, `cx`. Multiple allowed. On playbooks, can also appear per-scenario within body. |
| `impact` | enum | yes (playbooks), no (reports) | `critical` \| `high` \| `medium` \| `low` \| `informational`. Drives sort in `/lookup`, publishing gate, auto-suggest threshold. |

### Playbooks

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `scenarios` | `[string]` | yes | Scenario keys the playbook covers, e.g. `dlq-critical`. |
| `environments` | `[string]` | no | Where this applies: `eu-production`, `us-production`, `staging`, etc. Free-form; no taxonomy. |
| `last_verified` | ISO date | yes | When the playbook was last checked against reality. Drives staleness warnings in `/lookup`. |
| `source_notes` | `[path]` | no | Notes this playbook was extracted from. |
| `related_playbooks` | `[path]` | no | Cross-references to other playbooks (parent, child, sibling scenarios). |

### Ground-audits

Either embedded in another artefact's frontmatter or standalone.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `verifications` | object \| `[object]` | yes | Inline list of claim verifications, OR summary + ledger pointer. See structure below. |

Inline (small audits, ≤5 claims):
```yaml
verifications:
  - claim: "orders table has tenant_id column"
    source: "information_schema query 2026-04-17"
    confirmed: true
  - claim: "worker-service owns job-start topic"
    source: "cloud subscriptions list"
    confirmed: false
    correction: "internal-worker module handles job-start (inside worker-service repo)"
```

Summary + ledger (larger audits):
```yaml
verifications:
  confirmed: 23
  corrected: 2
  uncertain: 1
  ledger: queue_dlq_design_verification.md
```

## Subtype vocabulary

Validated against `taxonomy.subtype` enum. Default starting values:

| Type | Subtype values |
|------|---------------|
| note | `investigation`, `breakdown`, `scratch`, `postmortem`, `design`, `tooling`, `reference` |
| report | `problem-solution`, `analysis`, `outline`, `feature-release`, `handoff`, `post-mortem` |
| playbook | `scenario-playbook`, `runbook`, `reference` |
| ground-audit | `pre-artefact`, `standalone` |

Subtype maps directly onto the existing notes `category` field (for notes; rename). Projects can extend via `taxonomy.subtype` if new subtypes emerge.

## Taxonomy integration

`taxonomy.json` (per-project, lives under `$NOTES_DIR/taxonomy.json` — shared with reports and playbooks now) grows sections per field that needs vocabulary semantics:

```json
{
  "tags": {
    "optimisation": { "aliases": ["optimization"], "implies": ["performance"] },
    ...
  },
  "scope": {
    "messaging-service": { "aliases": ["msg-svc"], "implies": [] },
    "parser-service/pdf": { "aliases": [], "implies": ["parser-service"] }
  },
  "subtype": {
    "handoff": { "aliases": ["tier-handoff"], "implies": [] }
  },
  "enums": {
    "type": ["note", "report", "playbook", "ground-audit"],
    "status": ["shipped", "communicated", "revisiting", "monitoring"],
    "impact": ["critical", "high", "medium", "low", "informational"],
    "audience": ["operational", "technical", "engineering", "leadership", "on-call", "support-engineer", "cx"]
  }
}
```

Rules:
- **tags**: free write; normalised to canonical names; `implies` expanded at index time so queries match parents automatically.
- **scope**: free write; hierarchical implies (e.g., `x/y` implies `x`) applied automatically unless explicit implies block overrides.
- **subtype**: free write but validated against enum + aliases; unknown values raise a validator warning.
- **enums** (`type`, `impact`, `audience`): strict — unknown values are errors.

## Per-project architecture config (optional)

`agentic://projects/<project>/architecture.md`:
```yaml
---
architecture: microservices    # monorepo | microservices | library | multi-repo
component_term: service         # UI label
subcomponent_term: module
known_components:
  - messaging-service
  - worker-service
  - parser-service
---
```

Skills read this to present correct vocabulary and warn (not block) when `scope` values aren't in `known_components`. Absent config → no validation, generic "component"/"subcomponent" labels, free-form scope.

## ID derivation

Filename-based, computed on read:
- Strip directory path
- Strip `.md` extension
- Strip leading `YYYY-MM-DD_` prefix if present

Example: `working_notes/2026-04-17/skills_agents_design_discussion.md` → id = `skills_agents_design_discussion`.

No `id` field stored in frontmatter.

## Examples

### Note (investigation)
```yaml
---
type: note
subtype: investigation
date: 2026-04-17
tags: [bug-fix, investigation, queue, dlq]
scope: [messaging-service/queue, worker-service]
tickets: [gh:owner/repo#123]
related:
  - path: 2026-04-16/filename_encoding_bug.md
    relationship: context-for
---
```

### Note (split part)
```yaml
---
type: note
subtype: investigation
date: 2026-04-22
part: "2 of 3"
focus: "investigation evidence and trace analysis"
tags: [investigation, document-parser, overload]
scope: [document-parser]
tickets: ["pylon:340"]
related:
  - path: 2026-04-22/pylon_340_document_parser_overload_prod_incident_part_1.md
    relationship: context-for
---
```

### Report (handoff, engineering)
```yaml
---
type: report
subtype: handoff
date: 2026-04-17
status: shipped
audience: [engineering]
tags: [queue, dlq, escalation]
scope: [messaging-service/queue]
tickets: [jira:PROJ-456]
related:
  - path: working_notes/2026-04-17/queue_dlq_investigation.md
    relationship: extracted-from
---
```

### Playbook
```yaml
---
type: playbook
subtype: scenario-playbook
date: 2026-04-17
impact: critical
audience: [on-call, support-engineer]
tags: [queue, dlq, incident]
scope: [messaging-service/queue, parser-service, worker-service]
scenarios: [dlq-critical, dlq-parser, dlq-sync]
environments: [eu-production, us-production]
last_verified: 2026-04-07
source_notes:
  - working_notes/2026-04-17/queue_dlq_investigation.md
related_playbooks:
  - playbooks/parser-service/pdf/vector_graphics.md
---
```

### Ground-audit (standalone)
```yaml
---
type: ground-audit
subtype: standalone
date: 2026-04-17
scope: [messaging-service/queue]
related:
  - path: playbooks/messaging-service/queue/dlq.md
    relationship: context-for
verifications:
  - claim: "parser-process-batch max retries = 100"
    source: "cloud subscriptions list 2026-04-17"
    confirmed: true
---
```

## Validation rules (for graph_validator.py extension)

Validator exits non-zero if any **error** below; **warnings** are reported but non-blocking.

| Rule | Severity |
|------|----------|
| `type` missing or not in `taxonomy.enums.type` | error |
| `date` missing or not valid ISO `YYYY-MM-DD` | error |
| `subtype` missing | error |
| `subtype` not in `taxonomy.subtype` (after alias resolution) | warning |
| `impact` present but not in `taxonomy.enums.impact` | error |
| `status` present but not in `taxonomy.enums.status` | error |
| `status` missing on report (except roundup) | error |
| `audience` values not in `taxonomy.enums.audience` | error |
| `tags` value not in `taxonomy.tags` (after alias resolution) | warning |
| `scope` value not in project `architecture.md` known_components | warning (skip if absent) |
| `tickets` entry doesn't match `<source>:<id>` pattern | warning |
| `related.path` doesn't exist on disk | error |
| `related.path` points forward in time (DAG violation) for same-type links | error |
| `related.relationship` not in known set | warning |
| Playbook missing `scenarios` or `last_verified` | error |
| Playbook `last_verified` > 180 days old | warning |

## Migration from current schema

Existing notes under `$NOTES_DIR/`:

| Old field | New field | Migration action |
|-----------|-----------|------------------|
| `category` | `subtype` | rename; values unchanged (already match draft subtype enum for notes) |
| `tags` | `tags` | no change |
| `related_notes` | `related` | rename key; inner shape unchanged |
| (none) | `type` | add `type: note` to all existing notes |
| (none) | `date` | add from parent directory name (`YYYY-MM-DD/`) |
| (none) | `scope`, `tickets`, `audience`, `impact` | leave unset on legacy notes; populated going forward |

Migration script responsibilities:
1. For each existing note: add `type`, `date`, rename `category`→`subtype`, rename `related_notes`→`related`.
2. Update `taxonomy.json` to add `enums` and `subtype` sections (preserve existing `tags`).
3. Update `graph_validator.py` to the new rule set.
4. Re-run validator; fix any warnings surfaced.
