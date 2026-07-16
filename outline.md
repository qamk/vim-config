# Outline Reports

**Purpose**: Document how existing features, processes, or products work to enable knowledge transfer, onboarding, and operational support.

**When to Use**:
- Onboarding new team members (any role)
- Knowledge sharing across functions
- Creating support and operational guidance
- Documenting existing features without formal documentation

**Filename Convention**: `<subject>_<focus>_outline_report.md`
Examples: `invoice_workflow_operational_outline_report.md`, `appointment_scheduling_onboarding_outline_report.md`, `payment_processing_technical_onboarding_outline_report.md`

## Key Distinction from Feature Release

**Outline Reports** document **existing features** (any age) for knowledge transfer and operational support.

**Feature Release Reports** document **newly implemented features** before rollout for launch planning.

Use Outline when: Feature already exists and you need to explain how it works today.

## Collapsible Sections

Sections listed here should be wrapped in `<details>`/`<summary>` at authoring time. `/publish` handles per-adapter conversion.

| Variant | Collapsible Sections | Rationale |
|---------|---------------------|-----------|
| Operational | Support Guidance, Known Limitations | Reference material scanned for specific questions, not read end-to-end |
| General Onboarding | Troubleshooting, Business Context and History | Supplementary to the core "how does this work" narrative |
| Technical Onboarding | Technical Troubleshooting, Known Technical Debt and Future Work, How to Extend and Maintain | Reference sections, not the main learning path |

## Variant 1: Operational Outline Reports

**Target**: Customer Success, Support Teams, Account Managers, Project Managers
**Length**: 1.5-2 pages
**Tone**: Customer-focused, support-oriented, practical

**Purpose**: Enable CS/Support to effectively explain and support the feature to customers.

### Structure

1. **Feature Overview**
   - What the feature does (customer-facing perspective)
   - Who uses it and why
   - Primary business value

2. **Customer Value Proposition**
   - Problems this solves for customers
   - Benefits and outcomes
   - Why customers should care
   - Competitive advantages

3. **In Plain English**
   - How to explain the feature without jargon
   - Key talking points for customer conversations
   - Analogies or examples that resonate
   - How to position value proposition
   - *Use language-agnostic phrasing that translates across cultures*

4. **Support Guidance**
   - Common customer questions and answers
   - Troubleshooting scenarios
   - When to escalate to Engineering
   - Known issues and workarounds

5. **Known Limitations**
   - What the feature doesn't do
   - Edge cases to be aware of
   - How to explain limitations to customers
   - Workarounds or alternatives

6. **How Customers Access and Use It**
   - UI navigation and access methods
   - Required permissions or configurations
   - Step-by-step customer workflows
   - Prerequisites or dependencies

**Focus**: "How do I support customers using this?" — exclude all implementation details.

**Example**: Invoice workflow → How CS explains creation, common payment status questions, troubleshooting failures, communicating limitations.

## Variant 2: General Onboarding Outline Reports

**Target**: New hires (any role) learning the product
**Length**: 2-3 pages
**Tone**: Educational, comprehensive, exploratory

**Purpose**: Help new team members understand how features work and how they connect to the broader product.

### Structure

1. **Overview**
   - What the feature does (business perspective)
   - Why it exists (problem it solves)
   - Who uses it and in what context
   - Where it fits in the product ecosystem

2. **Connected Features and Systems**
   - Related features that work together
   - Dependencies and prerequisites
   - How data flows between features
   - Integration points with other systems
   - *Encourage exploration of related capabilities*

3. **How to Use It**
   - User workflows and journeys
   - Step-by-step instructions
   - Required configurations or settings
   - Permissions and access control
   - Common use cases and scenarios

4. **Implementation Overview** (High-Level)
   - How the feature works conceptually
   - Key components (no technical detail)
   - Business rules and logic
   - Data model (conceptual, not schema)
   - *Accessible to non-technical roles*

5. **Troubleshooting**
   - Common issues users encounter
   - How to diagnose problems
   - Resolution steps or workarounds
   - When to escalate and to whom

6. **Business Context and History**
   - Why this feature was built
   - Customer problems it addresses
   - Evolution and future roadmap
   - Key decisions or trade-offs made

**Focus**: "How does this work for users?" — exclude implementation details.

**Example**: Maintenance plans → What they are, connection to invoicing/scheduling, enrollment process, visit frequency rules, troubleshooting renewals.

## Variant 3: Technical Onboarding Outline Reports

**Target**: New engineers, developers, technical stakeholders learning the codebase
**Length**: 3-4 pages
**Tone**: Technical, implementation-focused, architecture-oriented

**Purpose**: Enable new engineers to understand, maintain, and extend the feature.

**Note for Planning**: Technical Onboarding reports may require codebase searches to locate file paths, trace execution flows, and identify integration points. Plan agents should account for this exploration work.

### Structure

1. **Technical Overview**
   - What the feature does technically
   - Key architectural decisions
   - Technology stack and dependencies
   - Design patterns used

2. **Architecture and Components**
   - System architecture diagram
   - Core components and their responsibilities
   - Module boundaries and separation of concerns
   - Domain model elements
   - Architecture principles applied

3. **Connected Systems and Integration Points**
   - Internal system dependencies
   - External service integrations (third-party services)
   - API contracts and protocols
   - Event flows and triggers
   - Data synchronization patterns

4. **Implementation Details**
   - **File Structure and Locations**:
     - Key files and their purposes
     - Package organization
     - Entry points and orchestration
   - **Database Schema**:
     - Tables, columns, relationships
     - Indexes and constraints
     - Foreign key dependencies
   - **API Endpoints**:
     - API routes and procedures
     - REST endpoints (if applicable)
     - Input/output schemas (validation library)
   - **Business Logic**:
     - Service layer implementations
     - Domain models and validation
     - Key algorithms and calculations
   - **Frontend Components** (if applicable):
     - React components and hooks
     - State management patterns
     - Form handling approaches

5. **How to Extend and Maintain**
   - Adding new capabilities
   - Modifying existing behavior
   - Common extension patterns
   - Testing strategy
   - Deployment considerations

6. **Technical Troubleshooting**
   - Debugging approaches
   - Common technical issues
   - Logging and observability
   - Performance considerations
   - Error handling patterns

7. **Known Technical Debt and Future Work**
   - Current limitations or constraints
   - Planned refactoring or improvements
   - Performance optimizations
   - Architecture evolution plans

**Include**: File paths, functions, database tables/columns, API endpoints, validation schemas, code snippets, architecture diagrams.

**Focus**: "How do I work with this code?"

**Example (Payment Processing):**
- Technical Onboarding: Architecture of payment flow, payment processor integration implementation in `infra-external-service/`, database schema for payment_records, API endpoints for payment creation, React form components, error handling patterns, how to add new payment methods.

## Modifiers

See `agentic://reports/modifiers.md` for all modifier definitions (`condensed`) and their transforms for this report type.

## When to Use Each Variant

**Operational Variant:**
- Training CS/Support on customer-facing features
- Creating customer support documentation
- Preparing for customer demos or sales calls
- Updating team on feature capabilities

**General Onboarding Variant:**
- Onboarding new team members (any role)
- Cross-functional knowledge sharing
- Product training across departments
- Documenting features for organizational memory

**Technical Onboarding Variant:**
- Onboarding new engineers to codebase
- Knowledge transfer when engineers leave
- Documenting complex technical features
- Preparing for major refactoring work

## Common Mistakes to Avoid

**All Variants:**
- Confusing with Feature Release (Outline = existing features, Release = new features)
- Too much focus on "why it was built" vs "how it works today"
- Missing troubleshooting guidance

**Operational Variant:**
- Including technical jargon or implementation details
- Not providing clear "how to explain to customers" guidance
- Forgetting common questions and limitations

**General Onboarding Variant:**
- Too technical for non-engineer audiences
- Not explaining connected features and context
- Missing business justification and history

**Technical Onboarding Variant:**
- Not enough implementation detail
- Missing file paths and code locations
- Unclear architecture or system boundaries
- Not documenting how to extend/maintain

## Success Criteria

**Operational Variant:**
- CS/Support can confidently explain feature to customers
- Common questions have clear answers
- Limitations and workarounds documented
- Escalation criteria clear

**General Onboarding Variant:**
- New hires understand feature purpose and context
- Connected features and workflows clear
- Basic troubleshooting possible without technical knowledge
- Business value and history understood

**Technical Onboarding Variant:**
- Engineers can locate and understand code
- Architecture and design patterns clear
- Integration points documented
- Extension and maintenance possible
- Debugging and troubleshooting effective
