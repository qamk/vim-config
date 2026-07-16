# Analysis Reports

**Purpose**: Evaluate existing features, products, or processes to identify gaps, opportunities, and improvements.

**When to Use**:
- Feature capability assessment
- Product area evaluation
- Process efficiency analysis
- Strategic planning for enhancements

**Filename Convention**: `<feature_name>_<focus>_analysis_report.md`
Examples: `maintenance_plans_feature_analysis_report.md`, `payment_processing_process_analysis_report.md`

## Status Field

**REQUIRED** in frontmatter. Enum: `shipped` | `revisiting` | `monitoring`. Default: `shipped`.

- **shipped** — analysis complete and delivered
- **revisiting** — analysis delivered but conclusions or recommendations are being reconsidered
- **monitoring** — recommendations acted on, watching outcomes before considering complete

Intermediate statuses (`planned`, `investigating`, `hypothesis`, `blocked`) belong to the roundup's curation workflow for issues that only have notes, not reports.

## Collapsible Sections

Sections listed here should be wrapped in `<details>`/`<summary>` at authoring time. `/publish` handles per-adapter conversion.

| Variant | Collapsible Sections | Rationale |
|---------|---------------------|-----------|
| Leadership | None | Already trimmed for leadership scanning |
| Technical | Individual gap/opportunity subsections within "Technical Gaps and Limitations" and "Technical Opportunities" | The overview + recommendations are the scan path; individual deep-dives are reference |

## Variant 1: Leadership Analysis

**Target**: CTOs, VPs Engineering, Department Heads, Executive Leadership
**Length**: 1.5-2 pages
**Style**: High-impact statements, strategic focus, bullet-heavy
**Tone**: Business-value oriented, ROI-focused, accessible to non-technical leadership

**Focus Areas**:
- Strategic importance and competitive positioning
- ROI and resource allocation
- Business impact metrics (ARR, support efficiency, customer retention)
- High-level technical context (no file paths, minimal implementation details)
- Organizational change management implications

**Exclude**:
- File paths and detailed code architecture
- Database table structures
- Step-by-step technical workflows
- Implementation-level details

### Structure

1. **Executive Summary** (max 3 paragraphs)
   - What exists today
   - What's lacking
   - Key findings
   - Improvement opportunities

2. **How Users Interact with the Feature/Process/Product**
   - Access methods
   - Requirements (configurations, settings, permissions)
   - User experience observations
   - Usage patterns (may require data analysis)
   - *Use subheadings to group capabilities, sub-features, or sub-processes*
   - *Include diagrams for complex flows*

   **Focus by Type:**
   - **Feature**: UI capabilities
   - **Process**: Information communication to users
   - **Product**: Accessibility, interactivity, completeness

3. **How the Feature/Process/Product Falls Short**
   - Current limitations
   - Gap analysis
   - Use cases not supported
   - User impact of gaps
   - Required changes (product, technical, CS perspectives)
   - *Use subheadings to group related gaps*
   - *Include diagrams showing missing capabilities*

4. **Product Comparison** (Current vs. Desired State)
   - Side-by-side comparison
   - Team implications (Product, CS, Marketing, Sales)

5. **Technical Architecture Comparison** (Current vs. Desired State)
   - Technical elements: UI, business logic, database, integrations
   - Implementation requirements

6. **Current Workarounds** (if applicable)
   - How customers currently bypass limitations
   - If none exist, state explicitly

7. **Immediate Opportunities**
   - **High-Impact, Low-Effort**: Quick wins
   - **High-Impact, High-Effort**: Strategic initiatives
   - Customer Success benefits for each

8. **Conclusion**
   - Summary of key findings
   - Strategic recommendations

**Example (Leadership):** "Maintenance plans lack seasonal pause, multi-location support. Serves ~60% of use cases. Quick win: seasonal toggle (1 sprint, retain $50K ARR). Strategic: multi-location (1 quarter, unlock $300K ARR)."

## Variant 2: Technical Analysis

**Target**: Senior/Staff Engineers, Architects, Principal Engineers, Technical Leads
**Length**: 2-3 pages
**Style**: In-depth technical evaluation, architecture-focused
**Tone**: Technical peer-level, assumes deep system knowledge

**Focus Areas**:
- Detailed architecture analysis and design patterns
- Implementation complexity and technical debt assessment
- Database schema design and data model implications
- Code organization and module boundaries
- Performance considerations and scalability concerns
- Migration paths and backward compatibility
- Integration points and API contracts
- Testing strategies and quality assurance approaches

**Include**:
- File paths and line numbers where relevant
- Code architecture diagrams
- Database schema comparisons
- API endpoint specifications
- Performance metrics and bottlenecks
- Technical constraints and trade-offs

### Structure

1. **Technical Overview** (2-3 paragraphs)
   - Current system architecture
   - Technical limitations and constraints
   - Key findings from code analysis

2. **Architecture Deep-Dive**
   - Core components and relationships
   - Database tables, columns, relationships, indexes
   - API endpoints, services, data flow
   - File locations and key functions
   - Integration points with other systems
   - Design patterns used
   - Code organization analysis

3. **Technical Gaps and Limitations**
   - Architectural constraints
   - Performance bottlenecks
   - Scalability concerns
   - Technical debt areas
   - Code quality issues
   - Missing abstractions or patterns
   - *Include file paths and specific code locations*

4. **Architecture Comparison** (Current vs. Desired State)
   - Technical elements: database schema, business logic, API layer, UI components
   - Migration complexity assessment
   - Backward compatibility requirements
   - Data transformation needs

5. **Implementation Requirements**
   - Development effort estimates by component
   - Technical dependencies and prerequisites
   - Testing requirements and strategies
   - Deployment considerations
   - Rollback strategies

6. **Technical Opportunities**
   - **Low-Complexity, High-Value**: Quick technical wins
   - **High-Complexity, High-Value**: Major architectural improvements
   - Development time estimates for each
   - Resource requirements (frontend, backend, database, DevOps)

7. **Recommendations**
   - Architectural approach suggestions
   - Technology stack considerations
   - Implementation sequence and phasing
   - Risk mitigation strategies

**Example (Technical):** "Maintenance plans use cron-based scheduler (src/services/ExampleService.ts). Lacks state machine for pause/resume. DB schema missing pause_start_date, pause_end_date columns. Quick win: add columns + pause logic (2-3 days, minimal schema migration). Complex: rebuild as event-sourced state machine (2-3 weeks, enables seasonal patterns, better audit trail)."

**Note:** For complex analyses requiring extended thinking, document findings in notes.

## Modifiers

See `agentic://reports/modifiers.md` for all modifier definitions (`condensed`) and their transforms for this report type.
