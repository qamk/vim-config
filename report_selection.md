# Report Type Selection Guide

Use this decision tree to select the appropriate report type:

```
START: What is your primary goal?

├─ Document a bug fix or feature change?
│  └─ Use: PROBLEM-SOLUTION REPORT
│     ├─ Audience includes Customer Success or non-technical stakeholders?
│     │  └─ Use: Non-Technical Audience variant
│     ├─ Audience is junior/mid-level engineers needing context?
│     │  └─ Use: Developing Engineers variant
│     ├─ Audience is senior engineers evaluating architecture?
│     │  └─ Use: Principal+ Engineers variant
│     └─ Audience spans technical and non-technical (including leadership)?
│        └─ Use: Mixed/Leadership variant
│
├─ Evaluate an existing feature or product area?
│  └─ Use: ANALYSIS REPORT
│     (Single variant: combines business and technical perspectives)
│
├─ Document how an existing feature or process works?
│  └─ Use: OUTLINE REPORT
│     ├─ Audience is operational (CS, Support, PM)?
│     │  └─ Use: Operational variant
│     ├─ Audience is new hires (any role)?
│     │  └─ Use: General Onboarding variant
│     └─ Audience is new engineers learning codebase?
│        └─ Use: Technical Onboarding variant
│
├─ Document a newly implemented feature for rollout?
│  └─ Use: FEATURE RELEASE REPORT
│     ├─ Audience is operational (CS, Support, PM)?
│     │  └─ Use: Operational variant
│     ├─ Audience is leadership (CTO, VPs, Executive)?
│     │  └─ Use: Leadership variant
│     └─ Audience is technical engineers who weren't involved?
│        └─ Use: Technical variant
│
├─ Summarise issues investigated or resolved over a time period?
│  └─ Use: ROUNDUP REPORT
│     (Single variant — no audience split)
│     Requires: --since and --until date range
│
└─ Transfer incomplete work between support tiers?
   └─ Use: HANDOFF REPORT
      ├─ Escalating to Tier 2 (Advanced Troubleshooting)?
      │  └─ Use: Tier 2 Handoff variant
      └─ Escalating to Tier 3 (Engineering)?
         └─ Use: Tier 3 Handoff variant
```

## When NOT to Create a Report

- **Trivial fixes**: Single-line changes, typo corrections
- **Work in progress**: Wait until investigation or implementation is complete
- **Duplicate coverage**: Check if a recent report already covers the topic
- **Insufficient information**: Gather context first via MCP tools or investigation
- **Incorrect tier assignment**: If ticket is in wrong tier, create handoff to correct tier instead of proceeding

## Determining and Verifying Ticket Tier

### Extracting Tier from issue tracker

**From Ticket Status:**
- Status pattern: **"Tier {1,2,3} {Triage,Backlog}"**
- Examples: "Tier 1 Triage", "Tier 2 Backlog", "Tier 3 Triage"
- Extract the tier number (1, 2, or 3) from the status

**From Custom Field:**
- Check the **"Support Tier"** custom field if status is unclear
- This field explicitly indicates the ticket's support tier

**Priority:** Use custom field "Support Tier" as the authoritative source if it conflicts with status.

### Verifying Tier Assignment

**Quick Verification Checklist:**
- Tier 1: Can I solve this with UI-only tools? No backend access needed?
- Tier 2: Do I need backend/DB access? Small code changes OK? NO database schema changes?
- Tier 3: Do I need database schema changes OR large/complex code changes OR architecture work?

If tier doesn't match complexity → See Tier Verification Protocol in agentic://references/investigation_workflow

### When Tier is Misassigned

If you determine the ticket is assigned to the wrong tier:
1. Document why in 2-3 sentences
2. Create tier-appropriate handoff report (not full investigation)
3. Stop investigation and hand off to correct tier

## Audience Value Propositions

Each report type serves distinct audiences with specific needs:

| Audience | Primary Role | What They Need | Report Purpose | Key Success Metric |
|----------|--------------|----------------|----------------|-------------------|
| **Non-Technical** | Customer Success, Project Managers, Marketing | Actionable customer communication guidance | Enable effective customer/stakeholder updates | They can explain issue/resolution to customers confidently |
| **Developing Engineers** | Junior/Mid-level Engineers, UI/UX Designers | Learning opportunities & investigation guidance | Build skills in codebase navigation & debugging | They can explore similar issues independently |
| **Principal+ Engineers** | Senior Engineers, Architects, Tech Leads | Architectural implications & decision support | Assess systemic risks and long-term solutions | They can evaluate solution quality and make informed decisions |
| **Mixed/Leadership** | CTOs, VPs Engineering, Department Heads | Strategic context & resource planning | Enable prioritization and resource allocation | They understand business impact and can allocate resources appropriately |
| **Operational (Feature Release)** | Customer Success, Support Teams, Project Managers | Rollout guidance, training needs, known limitations | Enable effective feature launch and customer support | They can confidently support and communicate the new capability |
| **Leadership (Feature Release)** | CTOs, VPs Engineering, Executive Leadership | Strategic value, rollout plan, organizational impact | Enable strategic decision-making and change management | They understand ROI, risks, and resource needs for successful rollout |
| **Technical (Feature Release)** | Senior/Staff Engineers, Architects (not involved in build) | Implementation details, architecture, integration points | Enable future maintenance and extension of the feature | They understand how it works and can build upon it |
| **Mixed (Roundup)** | Any stakeholder reviewing period activity | Scannable summary of issues, status, and patterns | Enable period review without reading every report | They can assess issue landscape and systemic patterns at a glance |
| **Tier 2 Support** | Advanced Troubleshooting, Backend Configuration | Complete investigation context to avoid duplicate work | Enable efficient backend investigation without repeating Tier 1 steps | They can pick up investigation immediately and identify root cause |
| **Tier 3 Engineering** | Engineering, Code-level Debugging | Comprehensive technical findings to enable code fixes | Enable targeted engineering work without re-investigation | They can implement fixes efficiently with full context |

## Technical Depth Guidelines by Audience

| Element | Non-Technical | Developing Engineers | Principal+ Engineers | Mixed/Leadership |
|---------|---------------|---------------------|---------------------|------------------|
| **Code snippets** | Rarely (if critical) | Frequently w/ explanation | Extensively | Sparingly (key points only) |
| **File paths** | Never | Always w/ line numbers | Always | Never |
| **Database details** | Only `display_id`, `guid` fields | Table/column names w/ relationships | Schema design & indexes | High-level data flow |
| **Architecture diagrams** | Simple ASCII if needed | Detailed w/ explanation | Comprehensive, minimal explanation | High-level strategic view |
| **Technical jargon** | Avoid entirely | Define on first use | Use freely | Minimize, define key terms |
| **Root cause depth** | Surface-level ("what broke") | Medium ("how it broke") | Deep ("why design allowed it") | Strategic ("impact & prevention") |
