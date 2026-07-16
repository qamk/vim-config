# Feature Release Reports

**Purpose**: Document newly implemented features for internal stakeholders to understand capabilities, plan rollout, and prepare for adoption.

**When to Use**:
- After feature implementation complete
- Before feature rollout to customers
- Internal communication about new capabilities needed
- Training materials required
- Known limitations need documentation

**Filename Convention**: `<feature_name>_release_report_<YYYY_MM_DD>.md`
Examples: `account_merge_release_report_2025_01_28.md`, `seasonal_maintenance_pause_release_report_2025_02_15.md`

## Collapsible Sections

Sections listed here should be wrapped in `<details>`/`<summary>` at authoring time. `/publish` handles per-adapter conversion.

| Variant | Collapsible Sections | Rationale |
|---------|---------------------|-----------|
| Operational | Known Limitations and Workarounds | Core value is "what's new"; limitations are supplementary reference |
| Leadership | Known Limitations and Future Roadmap | Core value is strategic; limitations are reference |
| Technical | Technical Limitations and Constraints | Core value is architecture and integration; limitations are reference |

## Key Differentiators

**Feature Release Reports are distinct from other report types:**

- **vs. Problem-Solution Reports**: Forward-looking (rollout planning) vs reactive (bug fixes)
- **vs. Analysis Reports**: Post-implementation vs pre-implementation evaluation
- **vs. Outline Reports**: Capability-focused (what's new) vs process-focused (how it works)
- **vs. Handoff Reports**: Stakeholder enablement vs work transfer between tiers

**Focus**: What's new, how to roll it out, who needs training, what are the limitations

## Variant 1: Operational Feature Release

**Target**: Customer Success, Account Managers, Project Managers, Support Teams
**Length**: 1.5-2 pages (comparable to Problem-Solution Operational reports)
**Tone**: Capability-focused, customer-impact oriented, training-ready

**IMPORTANT**: Only include specific timelines/dates in Rollout Plan section if provided by user. Do not assume or invent dates.

### Structure

1. **Feature Summary** (2-3 sentences)
   - What capability was added
   - Why it matters to customers
   - When it will be available

2. **What's New**
   - Core capabilities delivered
   - UI elements and access methods
   - Required configurations or settings
   - Permissions needed
   - Customer-facing changes
   - *Use subheadings for complex features*

3. **Business Value and Customer Impact**
   - Problems this solves for customers
   - Efficiency gains for customers or operations
   - Revenue or retention benefits
   - Customer experience improvements
   - Competitive advantages enabled

4. **Rollout Plan**
   - Timeline and phasing approach
   - Feature flags or gradual rollout strategy
   - Which customers get access when
   - Success criteria and metrics
   - Monitoring approach

5. **Training and Onboarding Needs**
   - Customer Success preparation required
   - Customer communication templates
   - Documentation updates needed
   - Common questions to prepare for
   - Demo or walkthrough materials

6. **Known Limitations and Workarounds**
   - Edge cases not yet supported
   - Constraints customers should know
   - Workarounds for unsupported scenarios
   - Future enhancements planned
   - When limitations will be addressed

7. **Support Preparation**
   - Common questions to expect
   - Troubleshooting scenarios
   - When to escalate to engineering
   - Known issues to watch for

**Focus**: "What can customers do?" and "How do we support them?" — exclude all implementation details (file paths, code, database, API endpoints).

**Example**: Account merge → Who can merge, what transfers, how to guide customers, handling failures, communication approach.

## Variant 2: Leadership Feature Release

**Target**: CTOs, VPs Engineering, Department Heads, Executive Leadership
**Length**: 1.5-2 pages (comparable to Problem-Solution Leadership reports)
**Tone**: Strategic, business-value focused, decision-support oriented

**IMPORTANT**: Only include specific timelines/dates if provided by user. Do not assume or invent dates.

### Structure

1. **Executive Summary** (2-3 paragraphs)
   - Strategic importance of this capability
   - Business impact and ROI
   - Key decisions made
   - Rollout approach

2. **Strategic Business Value**
   - Revenue impact (ARR growth, retention, expansion opportunities)
   - Operational efficiency gains (support reduction, time savings, automation)
   - Customer satisfaction and retention metrics
   - Competitive differentiation
   - Market opportunities enabled
   - Risk mitigation achieved

3. **What We Built**
   - High-level capability overview
   - **Include some technical context for CTO:**
     - System-level changes (e.g., "database functions", "API endpoints", "React components")
     - Architecture implications (e.g., "data scoping validation", "transaction boundaries")
     - Integration points (e.g., "third-party sync", "payment processing")
     - Data integrity measures (e.g., "audit trails", "snapshot capabilities")
   - Business logic and rules implemented
   - User experience changes
   - *Technical terms acceptable, but no code details*

4. **Rollout Strategy**
   - Phased deployment approach
   - Risk mitigation and rollback plan
   - Feature flags and gradual release
   - Success metrics and monitoring
   - Go/no-go criteria

5. **Organizational Impact**
   - Teams affected by this change
   - Training investment required
   - Process changes across departments
   - Change management considerations
   - Resource allocation needs
   - Timeline for full adoption

6. **Known Limitations and Future Roadmap**
   - Current constraints and why they exist
   - Scenarios not yet supported
   - Planned future enhancements
   - Timeline for addressing limitations
   - Technical debt considerations

7. **Success Metrics and KPIs**
   - How we'll measure success
   - Key metrics to track
   - Expected impact on business metrics
   - Monitoring and reporting approach
   - When to re-evaluate

### Technical Context (Leadership Balance)

| Include | Exclude |
|---------|---------|
| System-level terms ("database functions", "API endpoints") | File paths, line numbers |
| Architecture concepts ("data scoping isolation", "transactions") | Code snippets, function names |
| Integration names (third-party services) | Database column specifics |
| High-level patterns ("enables future dedup work") | Test counts, implementation details |

**Example**: "Database functions enable account consolidation with data scoping safety. Transaction boundaries ensure integrity. Snapshot system allows rollback."

## Variant 3: Technical Feature Release

**Target**: Senior/Staff Engineers, Architects, Tech Leads (who weren't directly involved in implementation)
**Length**: 2-2.5 pages (comparable to Problem-Solution Principal+ reports)
**Tone**: Technical, implementation-focused, architecture-oriented

**IMPORTANT**: Only include specific timelines/dates if provided by user. Do not assume or invent dates.

### Structure

1. **Technical Overview** (2-3 paragraphs)
   - What was built at technical level
   - Key architectural decisions
   - Systems and services affected
   - Integration points modified or added

2. **What We Built (Technical Detail)**
   - Database schema changes
     - New tables, columns, constraints
     - Indexes added for performance
     - Foreign key relationships
   - API endpoints (API)
     - New routes and procedures
     - Input validation schemas
     - Authentication/authorization changes
   - Services and business logic
     - New services created
     - Service modifications
     - Dependency injection changes
   - Frontend components (if applicable)
     - New UI components
     - State management changes
     - Form handling patterns
   - File paths for key components

3. **Architecture and Design Patterns**
   - Domain model elements
   - Architecture principles applied
   - Design patterns used (Repository, Service, etc.)
   - Multi-tenant safety measures
   - Error handling approach
   - Transaction boundaries
   - Data integrity mechanisms

4. **Integration Points**
   - Systems integrated with
   - API contracts and protocols
   - Dependencies added or modified
   - External service interactions (third-party accounting, payment processor, etc.)
   - Event flows and triggers

5. **Testing Strategy**
   - Unit test coverage
   - Integration test approach
   - Edge cases covered
   - Performance testing done
   - Test files locations

6. **Technical Limitations and Constraints**
   - Known technical debt
   - Performance considerations
   - Scalability concerns
   - Backward compatibility constraints
   - Future refactoring opportunities

7. **Rollout and Monitoring**
   - Feature flags and configuration
   - Deployment approach
   - Rollback strategy
   - Observability and logging
   - Metrics and monitoring
   - Error tracking

8. **Future Enhancements (Technical)**
   - Planned architectural improvements
   - Technical debt to address
   - Performance optimizations
   - Refactoring opportunities
   - Extensibility considerations

**Include**: File paths, functions, database tables, API endpoints, schema details, architecture diagrams, code patterns.

**Example**: SQL functions in `migrations/.../up.sql`, API framework router structure, test locations, snapshot depth levels, transaction patterns, data scoping validation.

## Modifiers

See `agentic://reports/modifiers.md` for all modifier definitions (`condensed`) and their transforms for this report type.

## When to Use Each Variant

**Operational Variant:**
- Preparing Customer Success for rollout
- Creating customer communication materials
- Training support teams
- Planning customer enablement

**Leadership Variant:**
- Executive briefings and decision-making
- Strategic planning and roadmap discussions
- Resource allocation decisions
- Organizational change management

**Technical Variant:**
- Onboarding engineers who will maintain/extend feature
- Architecture reviews and knowledge transfer
- Technical documentation for future work
- System design discussions

## Common Mistakes to Avoid

**All Variants:**
- **Including specific timelines/dates without user input** - Only add dates when provided by user
- Focusing too much on "how it was built" vs "what it enables"
- Omitting rollout plan and training needs
- Not documenting known limitations
- Missing business value and impact

**Operational Variant:**
- Including technical implementation details
- Using jargon (database, API, etc.)
- Forgetting support preparation section

**Leadership Variant:**
- Too technical (file paths, code) or not technical enough (CTO needs context)
- Missing strategic business value
- No success metrics or KPIs
- Omitting organizational impact

**Technical Variant:**
- Not enough implementation detail
- Missing file paths and code locations
- No testing strategy documented
- Unclear architecture patterns

## Success Criteria

**Operational Variant:**
- CS/Support can explain feature to customers
- Training materials can be created from report
- Known limitations clearly understood
- Rollout plan actionable

**Leadership Variant:**
- Executives understand strategic value
- Resource allocation justified
- Risk and change management clear
- Success metrics agreed upon

**Technical Variant:**
- Engineers can find and understand code
- Architecture decisions clear
- Integration points documented
- Future work well-scoped
