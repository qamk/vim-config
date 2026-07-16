# Report Modifiers

Reusable transforms applied on top of base report templates. Referenced by the `/report` skill or directly by the report-builder agent. Modifiers can be composed.

---

## Named Modifiers

### `condensed`

**Applies to**: Problem-Solution (Developing, Principal+), Analysis (all), Outline (all), Feature Release (all), Roundup
**Does not apply to**: Problem-Solution (Operational, Leadership), Handoff (all)

Condense to essential skeleton.

**Transforms**:

| Report Element | Standard | With `condensed` |
|----------------|----------|--------------|
| Section count | Full template | Core sections only (see below) |
| Bullets per section | Unlimited | 1-2 (max 3 for complex items) |
| Subsections | Allowed | None — flat list only |
| Code style (PS technical) | Full snippets with context | Diff-style only (`+`/`-` markers) |
| Target length | 1-3 pages | 0.5-1.5 pages |

**Core sections by report type**:

| Report Type | Variant | Core Sections |
|-------------|---------|---------------|
| Problem-Solution | Developing | Problem, Cause, Solution |
| Problem-Solution | Principal+ | Problem, Root Cause, Fix, Critical Edge Cases |
| Analysis | Leadership | Current State, Key Gaps, Recommendations, Action Items |
| Analysis | Technical | Current State, Key Gaps, Recommendations, Action Items |
| Outline | Operational | Feature Overview, What It Does, Known Limitations, How to Access |
| Outline | General | Overview, How to Use, Troubleshooting, Connected Features |
| Outline | Technical | Tech Overview, Implementation Details, How to Extend, Tech Debt |
| Feature Release | Operational | Feature Summary, What's New, Known Limitations, Rollout Plan |
| Feature Release | Leadership | Exec Summary, Strategic Value, Limitations/Roadmap, Success Metrics |
| Feature Release | Technical | Tech Overview, What We Built, Tech Limitations, Rollout/Monitoring |
| Roundup | (single) | Status Summary Table, Issues (compressed), Themes (bullets) |

---

### `diff-only`

**Applies to**: Problem-Solution (Developing, Principal+)

Show only code changes, no prose explanation of the code.

**Transforms**:

| Report Element | Standard | With `diff-only` |
|----------------|----------|-------------------|
| Code blocks | Full snippets with surrounding context | `+`/`-` diff markers, changed lines only |
| Code explanations | Prose paragraphs | 1-line comment above each diff block |
| Architecture context around code | Included | Skipped |
| Educational context for code | Included (Developing) | Skipped |

---

### `no-code`

**Applies to**: Problem-Solution (Developing, Principal+), Feature Release (Technical)

Remove code snippets, keep technical prose.

**Transforms**:

| Report Element | Standard | With `no-code` |
|----------------|----------|----------------|
| Code blocks | Included | Removed entirely |
| Inline code references | Implementation details in backticks | Described in prose instead |
| File paths and function names | In code blocks | Kept in prose |
| Architecture descriptions | Alongside code | Standalone — no code to reference |

---

### `by-theme`

**Applies to**: Roundup

Regroup issue entries under recurring-theme headings instead of chronological order.

**Transforms**:

| Report Element | Standard | With `by-theme` |
|----------------|----------|------------------|
| Issues section heading | "Issues" | "Issues by Theme" |
| Issue entry nesting | Flat numbered list | Nested under theme subheadings |
| Recurring Themes section | Full theme analysis | Shortened to cross-cutting patterns only |
| Issue numbering | Sequential | Preserved from status summary table (not renumbered) |

**Conflicts with**: `by-status`, `by-scope` (grouping modifiers are mutually exclusive)

---

### `by-status`

**Applies to**: Roundup

Regroup issue entries under resolution-status headings.

**Transforms**:

| Report Element | Standard | With `by-status` |
|----------------|----------|-------------------|
| Issues section heading | "Issues" | "Issues by Status" |
| Issue entry nesting | Flat numbered list | Nested under status subheadings (Shipped > Planned > Investigating > Hypothesis > Monitoring > Blocked) |
| Issue numbering | Sequential | Preserved from status summary table (not renumbered) |

**Conflicts with**: `by-theme`, `by-scope` (grouping modifiers are mutually exclusive)

---

### `by-scope`

**Applies to**: Roundup

Regroup issue entries under affected-service or area headings.

**Transforms**:

| Report Element | Standard | With `by-scope` |
|----------------|----------|------------------|
| Issues section heading | "Issues" | "Issues by Scope" |
| Issue entry nesting | Flat numbered list | Nested under service/area subheadings |
| Scope labels | N/A | Inferred from source material; uncategorisable items under "Other" |
| Issue numbering | Sequential | Preserved from status summary table (not renumbered) |

**Conflicts with**: `by-theme`, `by-status` (grouping modifiers are mutually exclusive)

---

## Composing Modifiers

Apply in order: **grouping** (`by-theme`, `by-status`, `by-scope`) → **length** (`condensed`) → **format** (`diff-only`, `no-code`).

**Conflicts**: `diff-only` + `no-code` → `no-code` wins. `condensed` on non-applicable variants → ignored silently. Grouping modifiers (`by-theme`, `by-status`, `by-scope`) are mutually exclusive — if two are provided, reject with error.

---

## Adding New Modifiers

```markdown
### `modifier-name`

**Applies to**: [Report types and variants]

[One sentence — what this modifier does.]

**Transforms**:

| Report Element | Standard | With `modifier-name` |
|----------------|----------|----------------------|
| [element] | [default behaviour] | [modified behaviour] |

**Additional elements** (if any):
- [New sections, removed sections, tone shifts]
```

Update the composing section if the new modifier interacts with existing ones.
