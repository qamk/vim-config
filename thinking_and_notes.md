# Extended Thinking & Investigation Documentation

Claude Code provides three thinking modes with increasing computational budgets:

| Level | Trigger Phrases | Token Budget | Best For |
|-------|----------------|--------------|----------|
| **Basic** | "think" | ~10,000 | Routine analysis, straightforward bugs |
| **Megathink** | "think hard", "think deeply", "think about it" | ~20,000 | Complex issues, multi-system interactions |
| **Ultrathink** | "ultrathink", "think harder", "think intensely" | ~32,000 | Architectural deep-dives, systemic analysis |

## 🔥 Why Notes Are Critical

Complex work exceeds working memory capacity. Notes are not optional documentation—they are your external memory that:

1. **Prevent duplicate work** - Document what you discovered so neither you nor other tiers repeat the work
2. **Enable high-quality handoffs** - Notes provide the raw material for comprehensive handoff reports
3. **Support accurate reporting** - Notes capture technical details while fresh, ensuring report accuracy
4. **Maintain continuity** - Allow you to resume complex work across sessions without losing context
5. **Create traceability** - Connect data sources, queries, findings, and decisions for evidence-based conclusions

The quality of your notes directly determines the quality of all downstream artifacts: handoffs, reports, implementations, and architectural decisions.

## Note-Taking Protocol

**🔥 REQUIRED when extended thinking is activated at medium or maximum levels (megathink or ultrathink).**

**Document as you investigate - Don't wait until the end.**

**Location:** `$NOTES_DIR/YYYY-MM-DD/`

**Structure:**
- Create date-based directories: `$NOTES_DIR/YYYY-MM-DD/`
- Use short, lowercase filenames based on the task goal (e.g., `payment_reconciliation.md`)
- If notes exceed ~1200 words, split into parts: `task_name_part_1.md`, `task_name_part_2.md`, etc. Split semantically at `##` boundaries — each part should cover a distinct phase or concern (e.g., context/evidence, root cause, remediation), not just hit a word limit. Each part's frontmatter includes `part: "N of M"` and `focus:` (a ≤10-word label derived from its headings).
- Include task list under "Tasks" subheading immediately after title
- Optimize for both AI and human readability

**What to Document:**
- Database queries executed and results found
- Code paths explored (file paths with line numbers)
- Hypotheses tested and outcomes
- Configuration settings checked
- Data patterns discovered
- What was ruled out and why
- **Inline mermaid diagrams** when a flow, sequence, or causal chain is central to the findings (see below)
- **High-impact technical evidence** (see below)

### High-Impact Technical Evidence

Notes must include the actual commands, queries, and outputs that drove the investigation — not just summaries of what was found. Someone reading the notes should be able to reproduce the investigation steps.

**Include verbatim:**
- **CLI commands**: `gcloud logging read`, Langfuse fetch scripts, `kubectl` commands, `curl` calls — the exact command as run
- **SQL queries**: Full query text, not "checked the database"
- **Code snippets**: Relevant functions, error handlers, or config that explain the root cause or fix — include file path and line numbers
- **Key output excerpts**: JSON snippets, log lines, or table results that were significant
- **Negative findings**: Commands that returned zero results are often as important as positive ones — include the command and note the empty result

**For each piece of evidence, annotate:**
- **What was run** (the command/query)
- **What it showed** (key output, abbreviated if large)
- **Why it mattered** (how it advanced the investigation or changed direction)

**Example:**
```markdown
### Step 3: GKE Error Logs by trace_id
\`\`\`bash
gcloud logging read '
  resource.type="k8s_container"
  AND labels.trace_id="pear-abc123..."
  AND severity>=ERROR
' --project=fifthd-production --limit=30
\`\`\`

**Result: ZERO rows returned.**

**Significance**: The error was invisible when searching by trace_id label.
This meant the error was either not emitted with request context or needed
a different search strategy — led to the thread-based text search approach.
```

**Anti-patterns:**
- ❌ "Queried GKE logs for errors" (no command, no result)
- ❌ "Checked Langfuse trace" (what specifically was checked?)
- ❌ "Found the root cause in the database" (which query? what did it return?)

**Good pattern:** Verbatim command → key output → significance annotation

**Technical Solution Breakdowns:**
For non-trivial solutions, create a companion breakdown file: `task_name_breakdown.md` (no `_part_n` suffix, regardless of note splitting).

## 🔥 Before Starting Investigation: Search Existing Notes

Before beginning any investigation, search for existing notes that may provide valuable context:

**Search Strategy:**
1. Use filename patterns to identify potentially relevant notes
2. Start with **1 file** by default
3. Scale up based on investigation needs:
   - **2-3 files**: Investigation is moderately complex
   - **5+ files**: Investigation is highly complex OR requires broad context

**When to Draw in More Context:**
- (i) You are explicitly prompted to gather more context
- (ii) Investigation is difficult and additional information would help direct focus
- (iii) Your analysis is questioned or determined incorrect by user
  - Notes can serve as proof of accuracy or guide toward correct path
  - Cross-reference findings against documented patterns

**Search Location:** `$NOTES_DIR/`

**Example Search:**
```bash
find $PROJECT_ROOT/working_notes -name "*payment*" -o -name "*invoice*"
```

## Notes vs Reports: Critical Distinction

**CRITICAL**: Notes and reports serve different purposes and MUST be stored separately.

### Notes (`$NOTES_DIR/`)

**Purpose**: Working investigation findings, external memory for complex work

**Characteristics**:
- Created DURING investigation
- Raw evidence, queries, hypotheses
- Database results, code paths explored
- What was ruled out and why
- Informal, optimized for AI/human collaboration
- May be incomplete or in-progress

**Creation Method**:
- Main thread for simple investigations
- notes-documenter agent for complex work (megathink/ultrathink)

**Example Files**:
- `$NOTES_DIR/2025-10-16/proj_7662_qbo_customer_sync_investigation.md`
- `$NOTES_DIR/2025-10-16/proj_7662_reference.md`

### Reports (`$REPORTS_DIR/`)

**Purpose**: Formal deliverables for specific audiences

**Characteristics**:
- Created AFTER investigation completes
- Polished, audience-appropriate
- Follows tier-based workflow structure
- Complete, self-contained
- Professional quality, ready to share

**Creation Method**:
- **ALWAYS via report-builder agent** (NEVER main thread)
- References investigation notes as input
- Follows memory files for structure: agentic://reports/[report_type].md

**Example Files**:
- `$REPORTS_DIR/generated/problem_solution_reports/operational/proj_7662_*.md`
- `$REPORTS_DIR/generated/problem_solution_reports/technical_junior_mid/proj_7662_*.md`

### Common Mistake: Saving Reports in working_notes

**❌ INCORRECT**:
```
$NOTES_DIR/2025-10-16/proj_7662_problem_solution_nontechnical.md
```

**✅ CORRECT**:
```
Notes: $NOTES_DIR/2025-10-16/proj_7662_investigation.md
Report: $REPORTS_DIR/generated/problem_solution_reports/operational/proj_7662_qbo_customer_sync_issue.md
```

### Workflow Integration

**Investigation Flow**:
1. Search prior notes (context-navigator agent, or the `/investigate` skill's built-in `/lookup` step)
2. Conduct investigation (`/investigate` skill — runs complexity verification, playbook check, evidence gathering inline)
3. Document findings in notes (`/note` skill, or notes-documenter agent directly for complex work)
4. Generate formal reports (`/report` skill, which wraps report-builder)

**Notes inform reports; reports are not notes.**

### Agent Assignments

| Artifact Type | Agent | Location |
|--------------|-------|----------|
| Investigation notes | notes-documenter (if complex) OR main thread | `$NOTES_DIR/` |
| Formal reports | report-builder (MANDATORY) | `$REPORTS_DIR/` |

**Never save formal reports in working_notes directory.**
