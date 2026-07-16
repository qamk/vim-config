# Agent-Aware Planning Protocol

**Purpose**: Enforce systematic agent orchestration in all plan generation to prevent fragmented workflows and ensure consistent use of specialized capabilities.

**Core Principle**: **Every plan step must specify which agent executes it**, or explicitly state "main thread" if no agent is needed.

---

## Mandatory Plan Structure

Every plan generated via `ExitPlanMode` or similar mechanisms MUST follow this template:

```markdown
# [Plan Title]

## Step N: [Step Description]
- **Agent**: [agent-name] OR "main thread"
- **Memory**: @path/to/memory/file.md OR "none"
- **Output**: [expected artifacts]
- **Rationale**: [why this agent/approach]
```

### Template Fields

| Field | Purpose | Examples |
|-------|---------|----------|
| **Agent** | Who executes this step | **Memory** | Knowledge to reference | **Output** | What gets produced | File paths, decisions, artifacts |
| **Rationale** | Why this approach | "Complex investigation requires orchestration", "Pure function, no agent needed" - Quality gates needed (safety, standards, patterns)
- Multiple steps that could run concurrently

### Use Main Thread When:
- Task is trivial (read single file, simple verification)
- **Simple code changes**: 1-10 lines, single const/enum update, formatting fix
- No specialized capability required
- Agent overhead exceeds benefit (simple fixes, documentation updates)
- Immediate context needed from prior steps

**Default**: If uncertain, use agent. Context isolation prevents degradation.

**Token-Conscious Decision**: If change is simple enough to validate in main thread (~5 minutes), skip expensive agents. Save tokens for genuinely complex work.

---

## Plan Template Example

Every step must include: Agent, Memory, Output, Rationale. Use template from "Mandatory Plan Structure" above.

---

## Special Cases (MANDATORY Agents)

| Scenario | MUST Use | Memory | Rationale |
|----------|----------|--------|-----------|
| issue ticket investigation | `/investigate` skill | agentic://references/investigation_workflow | Complexity verification, playbook check, structured evidence gathering |
| Formal reports | report-builder (via `/report` skill) | agentic://reports/*.md | Never write reports in main thread |
| Code quality review | quality-enforcer | @platform/CLAUDE.md top 10 frustrations | Before commits with code changes |
| Destructive operations 
---

## Memory File References

**Format**: User-level `@~/.claude/path`, Project `@platform/.claude/path`, Code patterns `packages/backend/src/...`, None `none`

**When**: Always for specialized agents, always for patterns, never for trivial operations.

---

## Enforcement Mechanism

**Self-Check Before Finalizing**: Every step has agent/skill/main-thread assigned? Memory files referenced? Investigation uses the `/investigate` skill? Reports use the `/report` skill (report-builder)? Quality gates use quality-enforcer? Assignments match the decision framework?

Mandatory flows may be either skills (when orchestration happens in main thread) or agents (when a single isolated execution is appropriate).

**If any fails, revise before presenting.**

---

## Integration & Benefits

Enhances existing workflows with agent orchestration. Benefits: context isolation (prevents main thread degradation), consistency (same patterns across work), discoverability (explicit assignments), quality (specialized expertise), efficiency (parallel execution).

---

## Quick Reference

| Task Type | Agent / Skill | Memory Reference |
|-----------|---------------|------------------|
| Ticket investigation | `/investigate` skill | agentic://references/investigation_workflow |
| Formal reports | report-builder (via `/report` skill) | agentic://reports/*.md |
| Investigation notes | notes-documenter | agentic://references/thinking_and_notes |
| Code review | quality-enforcer | @platform/CLAUDE.md |
| Pre-commit safety | CLAUDE.md validation | claude-md-enforcer | @platform/CLAUDE.md |
| Prior context search | context-navigator | agentic://references/thinking_and_notes |
| SQL script generation | External API debugging | Data integrity validation | data-integrity-validator | Database schema (hasura/migrations/), FK relationships |
| API implementation | Database schema | React components | Code discovery 