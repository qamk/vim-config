# Edge Cases & Special Scenarios

## Multiple Related Tickets

When reporting on work spanning multiple tickets, choose the primary ticket for filename and list all related tickets in Motivation section with brief explanation of relationships.

## Cross-Category Reports

If a report spans multiple categories (e.g., both Problem-Solution and Analysis), choose the primary category based on main goal, borrow sections from secondary category as needed, and note the hybrid approach in the introduction.

## Insufficient Information Scenarios

If context is missing:
1. **Ask for ticket number/link** if not provided
2. **Use issue management tools** to gather issue context
3. **Request screen recording tools permission** if UX investigation would help
4. **Document assumptions** if proceeding without complete information

## Ticket Assigned to Wrong Tier

When you discover a ticket is assigned to the wrong tier during Tier Verification Protocol:

**Create a tier handoff (not a full investigation):**
- File naming: `<ticket_number>_handoff_to_tier_<N>.md`
- Indicate tier mismatch in Handoff Summary section
- Include brief rationale (2-3 sentences) explaining why current tier is inappropriate and what tier should handle it
- Include initial observations from ticket review
- Do NOT proceed with full investigation

**Example rationale:** "This ticket requires database schema changes to add new columns to the `jobs` table. Per Tier 2 criteria, database schema changes must be handled by Tier 3, even when accompanying code changes are small."

## Report Iteration & Feedback

When revising a report based on feedback: identify gap, assess audience fit, add (don't replace) content, use version naming (`_v2`, `_v3`), and document changes if helpful.

See agentic://references/report_iteration for detailed guidance.

## MCP Tools Integration

**issue management tools**: Read ticket details/comments/threads for issue history. Document findings in notes.

**screen recording tools**: View UX recordings/console logs/network traffic. Always ask permission first. Document findings in notes.

**Workflow**: Use issue management tools for ticket context → document → ask before screen recording tools if link present → document → integrate into report
