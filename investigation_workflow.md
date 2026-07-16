# Investigation Workflow by Tier

**Purpose**: Define investigation processes and reporting requirements for each support tier to ensure consistent documentation and seamless handoffs.

**Key Principle**: Higher tiers create **cumulative reports** - they produce all reports from lower tiers PLUS their own tier-specific report. This ensures complete documentation at every level.

## Tier Verification Protocol

**🔥 BEFORE starting any investigation, verify tier assignment matches issue complexity:**

**Tier Assignment Criteria:**

**Tier 1 Issues:**
- UI-only troubleshooting (no backend access needed)
- Basic configuration checks (settings, permissions visible in UI)
- Customer communication and guidance
- Issue reproduction without technical tools

**Tier 2 Issues:**
- Backend investigation (database queries, logs, API testing)
- Advanced configuration analysis
- Small code changes (few lines across one or small number of files)
- Simple code changes (basic filtering logic, maps, new field, similar difficulty)
- **EXCLUDES: Database schema changes** (escalate to Tier 3)

**Tier 3 Issues:**
- Database schema changes (even if accompanying code changes are small)
- Large or complex code changes
- Architecture analysis or design changes
- Multi-system integration debugging
- Performance optimization requiring code-level changes

**Verification Steps:**

1. **Check ticket tier** (issue status: "Tier X Triage/Backlog" or "Support Tier" field)
2. **Assess issue complexity** against criteria above
3. **Verify you have required capabilities** for this tier
4. **If mismatch detected:**
   - Document mismatch in 2-3 sentences (why current tier inappropriate, what tier should handle)
   - Create handoff to correct tier (may be upward, lateral, or downward)
   - Include initial observations but do NOT proceed with full investigation

**Common Mismatch Signals:**
- Tier 1 ticket requires database queries → Handoff to Tier 2
- Tier 2 ticket requires database schema changes → Handoff to Tier 3
- Tier 2 ticket requires large/complex code changes → Handoff to Tier 3
- Tier 3 ticket is pure configuration → Handoff to Tier 2
- Any tier ticket is simple UI fix → Handoff to Tier 1

## Investigation Planning Requirements

**CRITICAL**: All investigations MUST follow agent-aware planning structure per agentic://references/planning_protocol

### Required Skills & Agents for Investigation Workflows

**1. Investigation Orchestration**
- **Skill**: `/investigate`
- **When**: ALL issue ticket investigations
- **Purpose**: Complexity verification, playbook short-circuit, structured evidence gathering, downstream skill recommendations — run inline in main thread
- **Memory**: agentic://references/investigation_workflow

**2. Context Search** (when `/investigate`'s built-in `/lookup` step is insufficient)
- **Agent**: context-navigator
- **When**: Need broader prior context than `/lookup` surfaced
- **Purpose**: Search prior notes, prevent duplicate work
- **Memory**: agentic://references/thinking_and_notes

**3. Notes Documentation**
- **Skill**: `/note` (delegates to notes-documenter for long/complex notes)
- **When**: Extended thinking activated, or any complex investigation needing external memory
- **Purpose**: Create investigation notes as external memory
- **Memory**: agentic://references/thinking_and_notes
- **Output**: ~/$PROJECT/working_notes/YYYY-MM-DD/ticket_name.md

**4. Report Generation**
- **Skill**: `/report` (wraps report-builder)
- **When**: MANDATORY for all formal reports
- **Purpose**: Generate problem-solution, handoff, analysis reports
- **Memory**: agentic://reports/[report_type].md
- **Output**: ~/$PROJECT/reports/generated/[report_category]/ticket_name.md

### Investigation Workflow Pattern

```markdown
## Step 1: Run /investigate
- **Skill**: `/investigate <ticket-or-description> [flags]`
- **Memory**: agentic://references/investigation_workflow
- **Output**: Complexity band verified, playbook checked, evidence gathered, downstream skills recommended
- **Rationale**: Single entry point for ticket investigations — handles prior-context lookup, complexity verification, and evidence gathering in one flow

## Step 2: Broader Context Search (only if needed)
- **Agent**: context-navigator
- **Memory**: agentic://references/thinking_and_notes
- **Output**: Additional prior notes, related tickets
- **Rationale**: Only invoke if `/investigate`'s built-in `/lookup` step did not surface enough context

## Step 3: Document Findings (if complex)
- **Skill**: `/note <topic> [--ticket=<ref>] [--with-breakdown]`
- **Memory**: agentic://references/thinking_and_notes
- **Output**: ~/$PROJECT/working_notes/YYYY-MM-DD/investigation.md
- **Rationale**: Complex investigations require external memory; `/note` delegates to notes-documenter for long content

## Step 4: Generate Formal Reports
- **Skill**: `/report <variant> [--ticket=<ref>]`
- **Memory**: agentic://reports/problem_solution.md
- **Output**: Tier-appropriate reports per workflow requirements
- **Rationale**: MANDATORY - Never write reports directly; `/report` wraps report-builder
```

### Critical Rules

1. **ALWAYS use the `/investigate` skill** for ticket investigations
2. **ALWAYS use the `/report` skill (report-builder)** for formal reports (not main thread)
3. **ALWAYS use `/note` (notes-documenter)** for extended-thinking or otherwise complex investigations
4. **ALWAYS search prior context** before starting complex work — `/investigate` does this via `/lookup` by default

**Violation**: Writing reports directly in main thread creates inconsistent quality and bypasses the tier-based workflow.

## Investigation Decision Flow

```
Investigation Start
│
├─ 🔥 VERIFY TIER ASSIGNMENT ──────────────┐
│  (Use Tier Verification Protocol)        │
│  │                                        │
│  ├─ Correct tier? → Continue              │
│  │                                        │
│  └─ Wrong tier? → Create handoff to ──────┘
│     correct tier, STOP investigation
│
├─ Tier 1 Investigation
│  │
│  ├─ Can resolve? ────────────────────┐
│  │  └─ YES → Create Reports:         │
│  │     • Non-Technical Problem-Solution Report
│  │                                    │
│  └─ Cannot resolve? ──────────────────┤
│     └─ NO → Create Reports:          │
│        • Tier 2 Handoff Report       │
│        └─ Escalate to Tier 2 ─────────→
│                                       │
├─ Tier 2 Investigation                 │
│  │                                    │
│  ├─ Can resolve? ────────────────────┤
│  │  └─ YES → Create Reports:         │
│  │     • Non-Technical Problem-Solution Report (Tier 1)
│  │     • Junior-Mid Technical Problem-Solution Report (Tier 2)
│  │                                    │
│  └─ Cannot resolve? ──────────────────┤
│     └─ NO → Create Reports:          │
│        • Tier 3 Handoff Report       │
│        └─ Escalate to Tier 3 ─────────→
│                                       │
└─ Tier 3 Investigation                 │
   │                                    │
   └─ Always resolves → Create Reports: │
      • Non-Technical Problem-Solution Report (Tier 1)
      • Junior-Mid Technical Problem-Solution Report (Tier 2)
      • Senior+ Technical Problem-Solution Report (Tier 3)
                                        │
                                        ↓
                                   Complete
```

## Tier 1: Frontline Support

**Before Beginning:** Verify this issue matches Tier 1 criteria using Tier Verification Protocol. If mismatch detected, create handoff to appropriate tier.

**Responsibilities:**
- UI troubleshooting
- Basic configuration checks
- Customer communication
- Initial problem identification

**Investigation Outputs:**

**If Investigation Completes:**
- ✅ **1 Report**: Non-Technical Problem-Solution Report

**If Escalation Required:**
- ✅ **1 Report**: Tier 2 Handoff Report

**Decision Criteria for Escalation:**
- Requires backend access or database queries
- Technical complexity beyond UI troubleshooting
- Needs advanced configuration changes
- Issue reproduction requires technical tools

## Tier 2: Advanced Troubleshooting

**Before Beginning:** Verify this issue matches Tier 2 criteria using Tier Verification Protocol. If mismatch detected (especially if database schema changes required), create handoff to appropriate tier.

**Responsibilities:**
- Backend investigation (database queries, log analysis, production data verification)
- Configuration analysis (company_config, feature flags, settings)
- API endpoint testing (manual testing, Postman/curl verification)
- SQL scripts (data corrections, backfills - company-specific or system-wide)
- **Minor code changes**:
  - 1-10 lines across 1-3 files
  - Simple validation logic, filtering, mapping, formatting
  - Const/enum additions (e.g., new appointment types)
  - Whitespace/string handling fixes (e.g., .trim())
  - Minor bug fixes not requiring architectural changes
  - Simple error handling improvements
- **EXCLUDES**:
  - Database schema changes (DDL - escalate to Tier 3)
  - Architectural refactoring (multiple systems - escalate to Tier 3)
  - Complex multi-file changes (5+ files - escalate to Tier 3)
  - Critical system modifications (auth, payments, integrations - escalate to Tier 3)

**Investigation Outputs:**

**If Investigation Completes:**
- ✅ **2 Reports**: Complete documentation suite
  1. Non-Technical Problem-Solution Report (Tier 1 perspective)
  2. Junior-Mid Technical Problem-Solution Report (Tier 2 perspective)

**If Escalation Required:**
- ✅ **1 Report**: Tier 3 Handoff Report

**Decision Criteria for Escalation:**
- Requires code changes beyond simple fixes
- Architecture or design issue identified
- Database schema modifications needed
- Integration or system-level debugging required
- Performance optimization needed

**Tier 2 Code Change Validation:**

When Tier 2 includes minor code changes:

1. **Main thread validates**:
   - Data scoping safety (scope identifier filtering where applicable)
   - Type safety (TypeScript compilation passes)
   - Test coverage (existing unit tests pass)
   - Pattern consistency (matches nearby code style)

2. **Use quality-enforcer agent** (optional):
   - Before committing customer-facing changes
   - When touching integration code (third-party integrations, Tilled, webhooks)
   - If uncertainty about pattern correctness

3. **Skip claude-md-enforcer** (expensive):
   - Simple fixes don't warrant ~100k token review
   - Main thread + quality-enforcer sufficient for Tier 2 scope

4. **Escalate to Tier 3 if**:
   - Code change reveals architectural issue
   - Fix requires touching multiple systems
   - Schema changes needed
   - Complexity exceeds Tier 2 scope (5+ files, critical systems)

## Tier 3: Engineering

**Before Beginning:** Verify this issue matches Tier 3 criteria using Tier Verification Protocol. If mismatch detected, create handoff to appropriate tier.

**Responsibilities:**
- Code-level debugging
- Architecture analysis
- Database schema changes (even if accompanying code changes are small)
- Integration fixes
- Performance optimization
- Complex system issues
- Large or complex code changes

**Investigation Outputs:**

**🚨 MANDATORY: Always Creates (No Further Escalation):**
- ✅ **3 Reports**: Complete documentation suite
  1. Non-Technical Problem-Solution Report (Tier 1 perspective)
  2. Junior-Mid Technical Problem-Solution Report (Tier 2 perspective)
  3. Senior+ Technical Problem-Solution Report (Tier 3 perspective)

**CRITICAL:** These reports are REQUIRED deliverables, not optional. Create them immediately after completing investigation/implementation, BEFORE considering the work complete.

**Note:** Tier 3 never creates handoff reports - they are the final tier.

## Best Practices

**For All Tiers:**
- **🔥 For complex work requiring extended thinking (megathink/ultrathink), CREATE detailed notes as you work** - Notes serve as external memory and prevent duplicate work
- Create reports immediately after completing investigation
- Include ticket references in all reports
- Document what was ruled out to prevent duplicate work
- Use consistent naming conventions
- Store reports in designated directories

**When Writing Multiple Reports (Tier 2 & 3):**
- Write reports in order: Non-Technical → Junior-Mid → Senior+
- Each report should stand alone for its target audience
- Don't reference other reports within the content
- Adjust technical depth appropriately for each audience
- Non-technical report focuses on customer impact
- Technical reports progressively add implementation details
- **Reference your investigation notes to ensure complete technical coverage**

**When Escalating:**
- Complete handoff report before escalation
- **Reference your investigation notes to ensure all findings are included**
- Include all investigation findings
- Document what was attempted and ruled out
- Provide clear next steps for receiving tier
- Ensure all supporting evidence is included
