# Universal AI Reporting Standards

This document contains universal patterns and workflows for AI-assisted technical reporting, applicable across projects and organizations.

agentic://references/path_variables
agentic://references/common_mistakes
agentic://references/success_criteria
agentic://references/report_iteration

<!-- Loaded on-demand (intentionally NOT @-imported here, to keep idle context small):
  agentic://references/investigation_workflow   → reachable via /report (report_selection.md); /investigate is self-contained
  agentic://references/database_query_patterns  → referenced by /investigate skill + data-integrity-validator agent
  agentic://references/search_tool_patterns     → referenced by context-navigator, notes-documenter, /investigate (main-thread rule below) -->

**Search tooling**: in Claude Code sessions, use the Grep tool (ripgrep) for local search — not Bash `grep`/`rg`.

## Task Orchestration: TODO Lists & Agent Delegation

**CRITICAL**: For any non-trivial task, create a TODO list first, then delegate to agents wherever possible.

### Why This Matters

- **TODO lists** make progress visible, resumable across sessions, and auditable
- **Agent delegation** isolates complex work, prevents context bloat, and brings specialised expertise
- **Parallel agents** dramatically reduce wall-clock time for independent steps
- **Main thread** stays lean — orchestrating agents rather than doing all the work itself

### Protocol

1. **Break work into discrete steps** — use TaskCreate for each
2. **Assign each step** to the most appropriate agent or explicitly mark "main thread"
3. **Launch independent agents in parallel** — if steps don't depend on each other, run them simultaneously
4. **Track progress** — update tasks as they start and complete
5. **Delegate generously** — if an agent exists for a task category, use it instead of doing the work in main thread

### When to Create TODO Lists

- Implementation tasks (3+ steps)
- Investigation workflows (always)
- Multi-file changes
- Any work that might span sessions or benefit from progress tracking

### When to Delegate to Agents

- Specialised expertise is available (SQL safety, architecture review, reporting, quality enforcement)
- Work benefits from isolated context (prevents main thread bloat)
- Multiple independent steps can run concurrently
- Complex analysis that would consume excessive main thread context

### Anti-Patterns

- Doing everything in main thread when agents exist for the task
- Sequential agent calls when they could run in parallel
- Skipping TODO lists for complex work ("I'll just remember")
- Creating TODO lists but not updating them as work progresses

## Skill Utilisation

Skills are specialised capabilities that appear in `<system-reminder>` tags. All agents and the main thread can invoke them via the `Skill` tool. Before starting work, check if any listed skills are relevant to the task — a skill that handles part of the work should be preferred over doing it manually.

### Diagram Generation

ASCII diagrams are inline conversation output — use freely without skill invocation, following `agentic://references/core_principles` Visual Elements Guidelines. For file-based outputs (HTML, Mermaid, Excalidraw, Figma), use the `/diagram` skill. It routes by intent (explain → HTML, ideate → Excalidraw, embed → Mermaid, mockup → Figma), generates audience-appropriate variants (`_operational`, `_technical`, `_leadership`), and saves to `$DIAGRAMS_DIR/{topic}/`.

## User-Level Agents (Dynamic Model Selection)

**Purpose**: Specialized agents for quality control, process orchestration, and documentation that complement the memory structure.

**Memory vs Agents:**
- **Memory files** (this directory) = Knowledge base (WHAT, WHY, WHEN)
- **Agents** (`agentic://agents/`) = Execution engines (HOW to do tasks)

**Model Selection Framework (Opus 4.5):**
- **Haiku**: Speed-critical safety checks, fast routing/search (~$0.25/$1.25 per million tokens)
- **Sonnet**: Fallback for simple tasks or budget constraints (~$3/$15 per million tokens)
- **Opus**: DEFAULT for most agents. State-of-the-art for coding, reasoning, and agents. Uses 65-76% fewer tokens, often offsetting ~1.67x price premium (~$5/$25 per million tokens)

**Opus Default Rationale:** Opus 4.5 is only ~1.67x more expensive than Sonnet (not 3-5x as previously assumed) while delivering significantly better results with fewer tokens. For complex tasks, Opus is effectively cost-neutral or cheaper due to token efficiency. Use Opus by default; reserve Sonnet only for trivial tasks or strict budget constraints.

### Agent Categories & Usage

#### Quality & Safety Agents

**quality-enforcer** (Opus - quality critical)
- **Use when**: After implementation, before commits, during code review
- **Validates**: Top 10 frustrations, code patterns, SQL correctness, solution simplicity
- **MCP Tools**: None (relies on code analysis tools)
- **Trigger**: "Review this implementation" or after feature completion

**claude-md-enforcer** (Opus - architectural depth required)
- **Use when**: Complex architectural work (5+ files), multi-system impact, auth/payments/integrations, data boundary changes
- **Skip for**: Investigation-only, simple fixes (1-10 lines), const/enum updates, simple SQL scripts, documentation
- **Model**: Opus (default). Architectural compliance validation requires deep reasoning.
- **Token Budget**: ~100k tokens - expensive but justified for architectural safety
- **MCP Tools**: None (architectural validation)
- **Trigger**: MANDATORY at end of todo lists ONLY when complex code implemented

#### Investigation & Process Agents

Ticket and incident investigations run through the `/investigate` skill (see `agentic://skills/investigate/SKILL.md`). The skill itself handles complexity verification, playbook short-circuit, evidence gathering, and downstream skill recommendations — main thread executes it directly without a dedicated orchestrator agent.

**context-navigator** (Haiku - fast search/routing)
- **Use when**: Ticket hints at duplicate work, investigation stalled, complex system needing architecture context, keywords match patterns ("reminder system", "third-party sync", "multi-table update")
- **Skip when**: First step of investigation (start with Grep/Read), simple bugs, no hints of duplicates
- **Token Budget**: ~10k tokens
- **MCP Tools**: Wiki/docs (search, get page, list pages), Issue tracker (search)
- **Search Tools**: Use Grep tool (ripgrep) for local files first. See agentic://references/search_tool_patterns
- **Trigger**: "Search for context" when ticket suggests prior similar work

#### Reporting & Documentation Agents

**report-builder** (Opus - quality critical)
- **Use when**: After investigation completion, need formal documentation
- **Model**: Opus (default). Report quality benefits significantly from Opus capabilities.
- **Generates**: Problem-solution, analysis, outline, feature release, handoff reports
- **Invocation**: Prefer `/report` skill for structured modifier/override support. The skill parses arguments and delegates to report-builder with a well-formed prompt. See `agentic://skills/report/SKILL.md`.
- **Modifiers**: `pending`, `condensed`, `diff-only`, `no-code` — defined in `agentic://reports/modifiers.md`
- **MCP Tools**: Issue tracker (get issue for context), Wiki/docs (get page for related docs)
- **Trigger**: `/report <type> <variant> [--modifiers]` or "Generate report" after completing investigation

**notes-documenter** (Opus - documentation quality)
- **Use when**: ANY of these conditions (OR, not AND):
  - Extended thinking (megathink/ultrathink) activated
  - Comprehensive documentation needed
  - Technical breakdown or analysis required
  - Process analysis or workflow documentation
  - Multi-step work requiring external memory
- **Creates**: Investigation notes, technical breakdowns, evidence trails, process documentation
- **MCP Tools**: Wiki/docs (get page, search for context), Issue tracker (get issue for ticket details)
- **Trigger**: ANY single condition above is met - use proactively, don't wait for all conditions
- **Critical**: If you're creating detailed markdown documentation in main thread, you should be using this agent instead

#### Tier 2 Support Agents

**data-integrity-validator** (Opus - safety critical)
- **Use when**: Planning multi-table updates, detecting orphaned records, validating FK relationships
- **Model**: Opus (default). Data integrity validation is safety-critical; quality improvements justify default usage for all FK analysis.
- **Validates**: Referential integrity, cascade behaviors, cross-company violations
- **Analyzes**: Dependency graphs, orphaned records, impact of coordinated updates
- **Token Budget**: ~25-35k tokens per invocation
- **MCP Tools**: query-$PROJECT-prod-db (SELECT queries for FK analysis, schema inspection via information_schema)
- **Trigger**: "Validate data integrity" or before multi-table operations
- **Example**: PROJ-1002 job location data fix, account deletion impact analysis

### MCP Tool Integration for Agents

**CRITICAL (v2.0.30+)**: MCP tools are now available to sub-agents. When invoking agents, include relevant MCP tool suggestions in the prompt to enhance their capabilities.

#### When to Include MCP Tool Suggestions

**ALWAYS include when:**
- Agent needs external data (issue tickets, wiki/docs, database schema)
- Investigation requires context from prior work
- Report generation needs source material
- Schema inspection required for SQL script generation

**NEVER include when:**
- No external data sources needed
- Agent already has all context in prompt

#### MCP Tool Invocation Pattern

When invoking an agent, structure the prompt to explicitly mention available MCP tools:

```markdown
Prompt: "[Task description]

Available MCP Tools:
- [Tool category]: [Specific tools and their purpose]
- [Tool category]: [Specific tools and their purpose]

[Additional context or constraints]"
```

#### Example

```markdown
Prompt: "[Task] using [agent].

Available MCP Tools:
- Issue tracker: Get ticket details for context
- Wiki/docs: Get related documentation

[Constraints / return path]"
```

#### Read-Only MCP Tools Reference

**Issue Management (Read-Only):**
- **Issue tracker**: Get issue, search issues, get remote links, list projects, get transitions, look up users
- **Wiki/docs**: List spaces, get page, list pages in space, get comments (footer/inline), get descendants, search

**Database (Read-Only):**
- **query-$PROJECT-prod-db**: Execute SELECT queries only
  - Schema inspection: `SELECT * FROM information_schema.columns WHERE table_name = 'table_name'`
  - FK relationships: `SELECT * FROM information_schema.table_constraints WHERE constraint_type = 'FOREIGN KEY'`
  - Data validation: SELECT queries for existence checks, orphan detection, data validation
- **Note**: Only SELECT queries. No INSERT, UPDATE, DELETE, or DDL operations

#### Agent-to-MCP-Tool Quick Map

| Agent / Skill | Recommended MCP Tools | Use Case |
|-------|----------------------|----------|
| `/investigate` skill | Issue tracker (get issue, search) | Gather ticket context and related issues |
| context-navigator | Wiki/docs (search, get page), Issue tracker (search) | Find prior work and documentation |
| report-builder | Issue tracker (get issue), Wiki/docs (get page) | Source material for reports |
| notes-documenter | Wiki/docs (search, getPage), Issue tracker (get issue) | Context for documentation |
| data-integrity-validator | query-$PROJECT-prod-db (SELECT) | FK analysis via information_schema, orphan detection |

### Agent Usage Patterns

**Proactive Usage (Use Without Being Asked):**
1. **context-navigator** - Before starting complex work (when hints of duplicates exist)
2. **notes-documenter** - When ANY of: extended thinking activated, creating comprehensive docs, technical breakdown needed, process analysis, OR creating detailed markdown in main thread
3. 
### Workflow Integration

**CRITICAL: Agents CANNOT invoke other agents.** Main thread must orchestrate multi-agent workflows in sequence.

**Standard Investigation Flow (Main Thread Orchestrates):**
1. Start: invoke **`/investigate <ticket-or-description>`** (runs complexity verification, playbook check, evidence gathering inline)
2. Context: **context-navigator** (if the investigation reveals need for related notes/prior work that the skill's `/lookup` step did not surface)
3. Document: **`/note`** skill, or **notes-documenter** agent directly for complex findings requiring external memory
4. Report: **`/report`** skill (wraps **report-builder** for tier-appropriate formal documentation)

**Notes-Documenter Workflow (Main Thread Orchestrates):**

**CRITICAL: Always invoke context-navigator before notes-documenter to ensure proper knowledge graph connections.**

1. **Context Search FIRST:** Invoke **context-navigator**
   - Search for related notes/files using keywords from current work
   - Identify existing documentation that should be linked
   - Gather file paths for "Related Files" frontmatter

2. **Document SECOND:** Invoke **notes-documenter** with context
   - Provide related file paths from context-navigator
   - Notes-documenter includes these in frontmatter
   - Creates proper knowledge graph connections

**Example orchestration:**
```
Main Thread:
1. User: "Document findings from payment reconciliation investigation"
2. Invoke context-navigator with prompt:
   "Search for payment reconciliation notes.

   Available MCP Tools:
   - Wiki/docs: Search pages, get page content
   - Issue tracker: Search for related tickets"

3. Context-navigator returns: [payment_system.md, invoice_processing.md, PROJ-7123, wiki/page/456]
4. Invoke notes-documenter with prompt:
   "Document payment reconciliation findings.

   Related files: [payment_system.md, invoice_processing.md]

   Available MCP Tools:
   - Wiki/docs: Get page to reference existing docs
   - Issue tracker: Get issue PROJ-7123 for ticket details"

5. Notes-documenter creates note with proper connections and MCP-sourced context
```

**Standard Implementation Flow:**
1. Plan: Create todo list with implementation tasks
2. Code: Implement following TDD
3. Review: Use **quality-enforcer** before commit (includes architecture-level data scoping check)
4. Safety: Use 
### Multi-Agent Orchestration (Critical Limitation)

Agents cannot invoke other agents ([claude-code#4182](https://github.com/anthropics/claude-code/issues/4182)) — they can only *recommend* the next agent. Main thread invokes each agent in sequence, reading each one's output to decide the next.

### Agent Invocation Thresholds

**CRITICAL**: Match agent to task complexity to avoid over-engineering simple tasks.

**Threshold Definitions:**

| Threshold | Token Budget | Trigger Criteria | When to Use |
|-----------|-------------|------------------|-------------|
| **LOW** | ~5-10k | Use liberally for exploration, file finding, quick searches | Explore subagent, Haiku agents |

**Quick Decision Tree:**
```
1. Does it require finding files/patterns?
   → LOW: Use Explore subagent (Task tool with subagent_type=Explore)

2. Does it require understanding architecture?
   → MEDIUM: docs-analyzer

3. Does it require tracing implementation?

4. Does it require finding code examples?

5. Does it require complex SQL/integration/FK analysis?

6. Is it a quality gate (pre-commit, pre-destructive)?
   → MANDATORY: Always use regardless of complexity
```

**File Finding: Use Explore Subagent (NOT agents)**

The built-in `Explore` subagent type (accessed via Task tool) provides fast file pattern matching and codebase exploration. Use it for:
- "Find files matching X pattern"
- "Where is the implementation of Y"
- "What files contain Z keyword"

```javascript
// Use Task tool with Explore subagent for file finding
Task({ subagent_type: "Explore", prompt: "Find all the project API framework routers related to invoices" })
```

### Agent Selection Quick Reference

**Use this table for rapid agent selection during investigations and implementations:**

| Scenario | Agent | Threshold | Token Cost | MCP Tools | When to Use |
|----------|-------|-----------|------------|-----------|-------------|
| **Quality & Safety** |
| Review code before commit | quality-enforcer | MANDATORY | ~medium | None | After implementation, before commits, during code review |
| Validate complex code | claude-md-enforcer | MANDATORY | ~100k | None | ONLY after complex architectural work (5+ files, critical systems) |
| **Investigation & Process** |
| Start ticket investigation | `/investigate` skill | MEDIUM | ~medium | Issue tracker | Starting issue ticket investigations, tier assignment unclear |
| Search for prior context | context-navigator | MEDIUM | ~10k | Wiki/docs, Issue tracker | When ticket hints at duplicate work or need architectural context |
| **Reporting & Documentation** |
| Generate formal reports | report-builder (via `/report` skill) | MEDIUM | ~medium | Issue tracker, Wiki/docs | After investigation completion, need formal documentation |
| Generate feature release docs | report-builder (via `/report` skill) | MEDIUM | ~medium | Wiki/docs | After feature implementation, before rollout |
| Document complex findings | notes-documenter | MEDIUM | ~low | Wiki/docs, Issue tracker | Extended thinking results, comprehensive docs, technical breakdowns |
| **Tier 2 Support** |
| Validate data integrity | data-integrity-validator | HIGH | ~25-35k | query-$PROJECT-prod-db | Multi-table updates, orphaned records, FK relationship validation |
| **Architecture Discovery** |
| Understand architecture | docs-analyzer | MEDIUM | ~medium-high | None | Need architecture understanding BEFORE implementation |
| Find files/patterns | **Explore subagent** | LOW | ~5-10k | None | Quick file pattern matching, codebase exploration |

**Decision Framework**:
1. **Check threshold** - LOW tasks should use Explore subagent or main thread, not agents
2. **Match complexity** - Simple fix (~10 lines) = main thread; Moderate (3+ files) = MEDIUM agents; Complex (safety-critical) = HIGH agents
3. **Optimize for tokens** - Use expensive HIGH threshold agents only when complexity warrants
4. **Follow workflow patterns** - `/investigate` skill → `/note` (or notes-documenter) → `/report` (wraps report-builder); call context-navigator mid-flow only if prior context is needed beyond the skill's built-in `/lookup` step

### Investigation vs Documentation Agent Workflow

**For Code Investigation (Ultrathink/Megathink):**
2. Then `notes-documenter` to document findings (if complex)

**For Architecture Investigation (Ultrathink/Megathink):**
1. Use `docs-analyzer` to understand architecture
3. Then `notes-documenter` to document findings (if complex)

**Key Distinction:**
- **Documentation agents** (notes-documenter) = capture and organize findings
- **Ultrathink trigger** = use investigation agent FIRST, then documentation agent SECOND if results are complex

### Self-Reinforcement Pattern

Each agent includes instructions to remind users to use them again. This creates a self-reinforcing pattern that prevents the top 10 frustrations from recurring.

**Example:**
```
After quality-enforcer completes: "Use quality-enforcer again before the next commit."
```

### Context Isolation Benefits

Agents operate in isolated contexts, preventing:
- Main thread context degradation
- Need for compaction (which causes errors)
- Loss of efficiency as context fills
- Token waste on repeated information

Agents can process large amounts of data and return distilled insights to main thread.

### -Specific Project Agents

**Token-Intensive Agents** (Use strategically, not speculatively):

**docs-analyzer** (Opus - analysis quality)
- **Use when**: Need to understand architecture/patterns before implementation
- **Model**: Opus (default). Deep analysis benefits significantly from Opus capabilities.
- **Output**: Architecture explanations, system design insights
- **Token efficiency**: Targeted queries only - specify exact topic/module
- **Token Budget**: ~medium-high
- **Example**: "Explain invoice reminder architecture" vs "Tell me about invoices"

### Inline Scripts via Heredoc (Preferred for One-Time Tasks)

**Pattern**: Use inline scripts for one-time analysis, transformation, or data extraction instead of creating temporary files.

**✅ GOOD - Inline script (saves 5-10 tool calls)**:
```bash
python3 << 'PYTHON'
import os
import re

# One-time data extraction/analysis
for file in files:
    # ... analysis logic
    print(results)
PYTHON
```

**❌ BAD - Creating temporary files for one-time use**:
```bash
# Requires: Write, Bash, Read, cleanup
# 4+ tool calls vs 1 with inline script
```

### When to use each, and the rules

Inline heredoc for one-time work (analysis, transformation, extraction) — saves 5–10 tool calls. Persistent file only for reusable automation, complex iteration, documentation, or CI.

**Rules**: quote the delimiter (`<< 'PYTHON'`) to prevent shell interpolation; keep scripts under ~50 lines (else use a file); prefer heredoc for read-only analysis and files for write-heavy work. Python and Bash cover ~95% of cases.

## Expensive Agent Decision Framework

### Complexity-Based Triggers

**USE expensive agents when:**
- **Architectural changes**: Modifications affecting multiple systems/boundaries
- **Multi-file refactoring**: Changes spanning 5+ files or multiple packages
- **Critical system modifications**: Auth, data isolation, payment processing, third-party integrations
- **Complex business logic**: Intricate domain models, workflow engines, state machines
- **Important deliverables**: Production-critical features, customer-facing changes

**SKIP expensive agents when:**
- **Simple fixes**: 1-10 line changes, whitespace/formatting, simple validation
- **Single file updates**: Isolated const/enum additions, type definition extensions
- **Trivial configuration**: Feature flag additions, simple env var updates
- **Documentation only**: README updates, comment additions, doc file edits

### Situation-Based Triggers

| Agent | Cost | Use When |
|-------|------|----------|
| context-navigator | ~10k | Ticket hints at duplicates, investigation stalled, need architecture context |
| docs-analyzer | ~medium-high | Need architecture BEFORE implementation, unfamiliar module, complex refactoring. Use targeted queries. |
| quality-enforcer | ~medium | Before committing complex/critical changes, customer-facing features, sensitive areas (auth, payments, data isolation) |
| claude-md-enforcer | ~100k | Complex architectural work, multi-file refactoring, critical systems (auth, payments, integrations), significant PRs |

### Decision Examples

| Complexity | Example | Agent Decision |
|------------|---------|----------------|
| LOW | 1-line fix, const array | Main thread validates |
| HIGH | Architectural refactoring | quality-enforcer + claude-md-enforcer |
| VERY HIGH | Critical integration (third-party integrations, auth) | All relevant expensive agents |

## Plan Generation Protocol

**MANDATORY**: All plans generated via `ExitPlanMode` or similar mechanisms MUST follow agent-aware planning structure.

**Core Requirements**:
1. **Plan Output**: Every plan step must specify which agent executes it, or explicitly state "main thread"
2. **Plan Invocation**: Prompts to Plan agent must include agent selection guidance (which agents to consider, why agents needed/not needed)

### Planning Structure

agentic://references/planning_protocol

**Template**:
```markdown
## Step N: [Description]
- **Agent**: [agent-name] OR "main thread"
- **Memory**: @path/to/memory/file.md OR "none"
- **Output**: [expected artifacts]
- **Rationale**: [why this agent/approach]
```

### Agent Locations

**User-Level Agents**: `agentic://agents/`
- Cross-project capabilities (investigation, reporting, quality, safety)
- Examples: report-builder, quality-enforcer, context-navigator, data-integrity-validator

**Project-Level Agents**: `<project>/.claude/agents/`
- Project-specific capabilities (architecture, implementation patterns)

### Critical Rules

1. **Investigation workflows**: MUST use the `/investigate` skill (drives complexity verification, playbook check, evidence gathering, and downstream recommendations inline)
2. **Report generation**: MUST use report-builder (never write reports directly)
3. **Quality review**: MUST use quality-enforcer before commits with code changes
5. **CLAUDE.md validation**: MUST use claude-md-enforcer at end of todo lists ONLY when code was implemented (skip for investigation-only work)

**Violation of these rules degrades workflow quality and creates fragmentation.**

See agentic://references/planning_protocol for detailed template, examples, and decision framework.

## Database Investigation Patterns

**Reference**: agentic://references/database_query_patterns for comprehensive database query safety patterns.

### Always-on rules (full patterns in the on-demand doc)

- **Schema first**: check `information_schema` (or migration files) before any live query — never assume column names (camelCase vs snake_case).
- **Bound results**: COUNT before fetching; if > 20 rows, `LIMIT 20` inline and write a script (no LIMIT) for the full extract under `scripts/sql/{company}/` → CSV in `data/{company}/`. Scope to the tenant/company column unless system-wide is justified.
- **Multi-table**: map FK constraints in `information_schema`, LEFT JOIN to find orphans, count impact before any fix.

## -Specific Resources & Conventions

### SQL Scripts Directory Structure

**Location**: `~/$PROJECT/code/scripts/sql/`

**Organization**:
- **Company-Specific**: `scripts/sql/{company_name}/` - Single-company backfills/fixes. Naming: `proj_{ticket}_description.sql`
- **System-Wide**: `scripts/sql/_snippets/` - Multi-company operations, templated for reuse
- **General/Utility**: `scripts/sql/general/` - Analytics, cross-company queries

**Best Practices**: Include headers (context, root cause, impact), DRY RUN steps, rollback instructions, verification queries, expected row counts.
