# Handoff Reports

**Purpose**: Transfer incomplete investigation work between support tiers without duplicating effort.

**When to Use**:
- Escalating from Tier 1 (Frontline Support) to Tier 2 (Advanced Troubleshooting)
- Escalating from Tier 2 to Tier 3 (Engineering)
- Work is incomplete but requires specialized technical expertise
- Investigation has reached the limits of current tier's capabilities

**Filename Convention**: `<ticket_number>_handoff_to_tier_<N>.md`
Examples:
- `proj_1234_handoff_to_tier_2.md` (writing FOR Tier 2 to receive)
- `proj_5678_handoff_to_tier_3.md` (writing FOR Tier 3 to receive)

**Critical Principle**: "Engineering should not repeat previous steps" - clearly document what's been done, what's been ruled out, and what's needed next.

**Note:** Your notes provide the raw material for comprehensive handoffs, refer to investigation notes when creating these reports. For extracting and verifying ticket tier, see the report selection guide.

## Collapsible Sections

Sections listed here should be wrapped in `<details>`/`<summary>` at authoring time. `/publish` handles per-adapter conversion.

| Variant | Collapsible Sections | Rationale |
|---------|---------------------|-----------|
| Tier 2 Handoff | Supporting Evidence | The summary + next steps are the scan path; evidence is reference |
| Tier 3 Handoff | Supporting Evidence, Technical Findings | The summary + next steps are the scan path; detailed findings and evidence are reference |

## Variant 1: Tier 2 Handoff (from Tier 1)

**Target**: Tier 2 Support (Advanced Troubleshooting)
**Technical Depth**: Junior-mid level (explain technical concepts, avoid assumptions)
**Length**: 1.5-2 pages
**Tone**: Thorough, educational, action-oriented

**Structure:**

1. **Handoff Summary** (2-3 sentences)
   - Original customer issue in plain language
   - Why escalating to Tier 2 (what Tier 1 cannot resolve)
   - Priority level and SLA expectations

2. **Customer Request and Context**
   - Exact customer description (quote if helpful)
   - Ticket references (issue ticket number, support conversation link)
   - Account details: `account_id`, company name, account display ID
   - Business impact (how many users affected, revenue at risk, etc.)

3. **Tier 1 Investigation Completed**
   - UI elements checked and actions taken
   - Basic troubleshooting steps performed
   - Reproduction attempts and results
   - Customer communication history
   - Tools used (support platform, screen recording tool, issue tracker)

4. **Findings and Observations**
   - What Tier 1 discovered during investigation
   - screen recording session links with timestamps
   - Screenshots or screen recordings
   - Error messages visible to users
   - Patterns or anomalies noticed

5. **Ruled Out**
   - What was investigated but eliminated as cause
   - Why certain solutions didn't apply
   - Common fixes that were attempted unsuccessfully
   - **Purpose**: Prevents Tier 2 from repeating work

6. **Quick Wins** (if applicable)
   - Simple configuration changes to try
   - Temporary workarounds for customer
   - Easy fixes that might resolve the issue
   - Low-risk actions with potential high value

7. **Caveats and Constraints**
   - Customer-specific configurations or customizations
   - Access limitations Tier 1 encountered
   - Edge cases or unusual circumstances
   - Time-sensitive considerations

8. **Recommended Next Steps for Tier 2**
   - Backend systems to investigate
   - Configuration settings to check
   - Database queries that might be needed (describe in plain language)
   - Tools or permissions required
   - Estimated complexity (simple/medium/complex)

9. **Supporting Evidence**
   - issue ticket: [PROJ-1234](your-issue-tracker-url/PROJ-1234)
   - support conversation: [link]
   - screen recording sessions: [link with timestamp]
   - Relevant display IDs: `items.display_id`, `records.display_id`
   - Relevant GUIDs: `account_id`, `item_id`, `location_id`
   - Screenshots or recordings

**Example:** Structure includes Handoff Summary (2-3 sentences), Customer Request, Tier 1 Investigation (checklist), Findings (bullets), Ruled Out (specific items), Quick Wins (if any), Caveats, Next Steps (actionable for Tier 2), Supporting Evidence (GUIDs, screen recording tool links, issue tracker refs).

## Variant 2: Tier 3 Handoff (from Tier 2)

**Target**: Tier 3 Engineering
**Technical Depth**: Mid-senior+ level (assume technical knowledge, include code-level details)
**Length**: 2-3 pages
**Tone**: Technical, precise, comprehensive

**Structure:**

1. **Handoff Summary** (2-3 sentences)
   - Technical issue summary
   - Why escalating to Tier 3 (what Tier 2 cannot resolve)
   - Priority level and engineering impact assessment

2. **Original Request and Context**
   - Customer issue description
   - Ticket references (issue tracker, support platform)
   - Account/company details with GUIDs
   - Business and technical context
   - SLA implications

3. **Tier 1 + Tier 2 Investigation Completed**
   - UI troubleshooting completed (Tier 1 summary)
   - Backend investigation performed (Tier 2 detail)
   - Configuration settings checked
   - Database queries executed (include SQL)
   - API endpoints tested
   - Detailed reproduction steps

4. **Technical Findings**
   - System behavior observed
   - Relevant log entries and error messages
   - Database state for affected records
   - API request/response examples
   - File paths involved (if identified): `src/...`
   - screen recording sessions with console logs
   - Network traffic analysis (if applicable)

5. **Ruled Out**
   - Configuration issues eliminated (with evidence)
   - Code paths investigated and cleared
   - Integration points verified (third-party services)
   - Database integrity checks passed
   - **Be specific**: "Not X because we verified Y"

6. **Quick Fixes Attempted** (if applicable)
   - Database updates tried (include SQL)
   - Configuration changes attempted
   - Temporary patches considered
   - Results of each attempt

7. **Technical Caveats**
   - Multi-tenant implications (scope_id isolation)
   - Data integrity concerns
   - System dependencies and side effects
   - Edge cases discovered during investigation
   - Performance considerations

8. **Recommended Engineering Actions**
   - Specific code areas to investigate with file paths
   - Database schema considerations
   - Architecture review needed (if systemic issue suspected)
   - Required access or permissions for debugging
   - Estimated engineering effort (hours/days)
   - Suggested debugging approach

9. **Supporting Evidence**
   - issue ticket: [PROJ-XXXX](your-issue-tracker-url/PROJ-XXXX)
   - Database GUIDs for all affected records
   - File paths with line numbers (if known)
   - SQL queries executed (with results)
   - screen recording sessions with console logs
   - Related code commits or PRs (if relevant)
   - API logs or traces

**Example:** Structure includes Handoff Summary, Original Request (tickets, scope, SLA), Tier 1+2 Investigation (UI + backend with actual SQL queries), Technical Findings (root cause, DB evidence, file paths), Ruled Out (with evidence), Quick Fixes Attempted (SQL + results), Technical Caveats (data scoping, data integrity), Recommended Engineering Actions (immediate/required/long-term with estimates), Supporting Evidence (SQL queries, issue tracker links, screen recording sessions, commits).
