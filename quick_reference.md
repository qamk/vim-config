# Quick Reference

## Report Title Formatting

**Standard Format:**
`Report for issue <ticket summary> (ticket: [<ticket number>](<ticket link>))`

**Examples:**
- `Report for issue invoice rounding error (ticket: [PROJ-1234](your-issue-tracker-url/PROJ-1234))`
- `Report for issue payment sync failure (ticket: PROJ-5678)` *(no link available)*

**Ticket Summary Sources** (in priority order):
1. User-provided summary
2. Branch name context clues
3. issue ticket title

**Important:** If ticket number/link is unclear, **ASK before proceeding**.

## File Management Reference

### Report Storage Locations

**Base:** `$REPORTS_DIR/`

**Problem-Solution:**
- Operational → `problem_solution_reports/operational/`
- Developing Engineers → `problem_solution_reports/technical_junior_mid/`
- Principal+ Engineers → `problem_solution_reports/technical_senior_plus/`
- Leadership → `problem_solution_reports/leadership/`

**Analysis:**
- Leadership → `analysis_reports/leadership/`
- Technical → `analysis_reports/technical/`

**Outline:**
- Operational → `outline_reports/operational/`
- General Onboarding → `outline_reports/general_onboarding/`
- Technical Onboarding → `outline_reports/technical_onboarding/`

**Feature Release:**
- Operational → `feature_release_reports/operational/`
- Leadership → `feature_release_reports/leadership/`
- Technical → `feature_release_reports/technical/`

**Handoff:**
- Tier 2 → `handoff_reports/tier_2/`
- Tier 3 → `handoff_reports/tier_3/`

### Filename Conventions

**Rules**: Lowercase, spaces→underscores, ignore punctuation, include ticket if available: `<ticket_number>_<summary>.md`

**Augments**: Append `_<augment_name>` suffix before `.md` (e.g., `_quick`)

**Examples**: `proj_1234_invoice_rounding_error.md`, `proj_1234_invoice_rounding_error_quick.md`

**Variants**:
- Analysis (with ticket): `proj_<ticket>_<summary>_technical_analysis[_<augment>].md` (e.g., `proj_1005_z_index_mobile_portal_technical_analysis_quick.md`)
- Analysis (no ticket): `<feature>_<focus>_analysis_report.md` (e.g., `maintenance_plans_feature_analysis_report.md`)
- Outline: `<subject>_<focus>_(non_)technical_outline_report.md` (e.g., `payment_workflow_technical_outline_report.md`)
- Handoff: `<ticket>_handoff_to_tier_<N>.md` (e.g., `proj_1234_handoff_to_tier_2.md`)

### Working Notes Structure

**Location:** `$NOTES_DIR/YYYY-MM-DD/`

**Filename:** `<task_goal>.md` (short, lowercase, underscores)

**Splitting:** If >2000 words, use `<task_goal>_part_1.md`, `_part_2.md`, etc.

**Breakdown Files:** `<task_goal>_breakdown.md` (no `_part_n` suffix, regardless of note splitting)

## Report Structure Reference

**Problem-Solution:** Motivation → Problem(s) → Cause → Solution(s) → Conclusion. Variants add:
- **Operational**: Impact, Next Steps
- **Developing**: Files/Code, Technical Design (with explanations), Suitability
- **Principal+**: Technical Design (brief), Suitability
- **Leadership**: Impact, Suitability, Next Steps

**Analysis:**
- **Leadership**: Exec Summary → User Interaction → Gaps → Product Comparison → Current Workarounds → Opportunities → Conclusion
- **Technical**: Tech Overview → Architecture Deep-Dive → Tech Gaps → Architecture Comparison → Implementation Requirements → Tech Opportunities → Recommendations

**Outline:**
- **Operational**: Feature Overview → Customer Value → Plain English → Support Guidance → Limitations → Access
- **General Onboarding**: Overview → Connected Features → How to Use → Implementation Overview → Troubleshooting → Business Context
- **Technical Onboarding**: Tech Overview → Architecture → Integration Points → Implementation Details → Extend/Maintain → Troubleshooting → Tech Debt

**Feature Release:**
- **Operational**: Feature Summary → What's New → Business Value → Rollout Plan → Training Needs → Limitations → Support Prep
- **Leadership**: Exec Summary → Strategic Value → What We Built → Rollout Strategy → Org Impact → Limitations/Roadmap → Metrics
- **Technical**: Tech Overview → What We Built → Architecture/Patterns → Integration Points → Testing → Limitations → Rollout/Monitoring → Future Enhancements

**Handoff:**
- **Tier 2**: Summary → Customer Request → T1 Investigation → Findings → Ruled Out → Quick Wins → Caveats → Next Steps → Evidence
- **Tier 3**: Summary → Original Request → T1+T2 Investigation → Technical Findings → Ruled Out → Quick Fixes → Caveats → Engineering Actions → Evidence

## Report Length Guidelines

| Type | Length (pages) |
|------|----------------|
| **Problem-Solution**: Operational | 1-1.5 |
| **Problem-Solution**: Developing Engineers | 1.5-2.5 |
| **Problem-Solution**: Principal+ | 2-3 |
| **Problem-Solution**: Leadership | 1.5-2 |
| **Analysis**: Leadership | 1.5-2 |
| **Analysis**: Technical | 2-3 |
| **Outline**: Operational | 1.5-2 |
| **Outline**: General Onboarding | 2-3 |
| **Outline**: Technical Onboarding | 3-4 |
| **Feature Release**: Operational | 1.5-2 |
| **Feature Release**: Leadership | 1.5-2 |
| **Feature Release**: Technical | 2-2.5 |
| **Handoff**: Tier 2 | 1.5-2 |
| **Handoff**: Tier 3 | 2-3 |

*~500 words/page.*

## Quick Mode Reference

**Trigger**: "quick", "brief", "summary" in request

| Report | Variants | Quick Target | Quick Focus |
|--------|----------|--------------|-------------|
| Feature Release | All | 0.5-1 pg | Core 4 sections |
| Outline | All | 0.5-1 pg | Core 4 sections |
| Problem-Solution | Developing, Principal+ | 0.75-1.5 pg | Diff-style code |
| Analysis | Leadership, Technical | 0.5-1 pg | Core 4 sections |

**Not applicable**: PS (Operational, Leadership), Handoff
