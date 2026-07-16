# Core Reporting Principles

## Universal Standards

1. **Objective Language**: Use factual, neutral tone without superlatives or excessive praise
2. **Heading Grammar**:
   - Use "The Problem" for singular issues, "The Problems" for multiple
   - All major headings in Title Case
3. **Technical Details**:
   - Code/database elements: Use exact representation (e.g., `records.display_id`)
   - Configurations: Document required permissions, settings, feature flags
4. **Clarity Over Cleverness**: Prioritize reader comprehension

## Visual Elements Guidelines

### Inline Diagrams (No Skill Required)

**ASCII diagrams** are the default for all audiences in conversation. Simple, fast, version-control friendly, accessible.

- Patterns: simple flow (`A → B → C`), decision tree (`├─ option A`, `└─ option B`), hierarchy (nested indents with connectors)
- Both the user and Claude can use ASCII freely in any response

### File-Based Diagrams (`/diagram` Skill)

For persistent, interactive, or presentation-quality output, use the `/diagram` skill. It generates self-contained files (HTML, Mermaid, Excalidraw, Figma) saved to `$DIAGRAMS_DIR/{topic}/`.

**Tool routing by intent:**

| Intent | Primary Tool | Fallback |
|--------|-------------|----------|
| Explain / educate | ASCII (inline) or HTML (file) | — |
| Ideate / brainstorm | Excalidraw MCP | HTML with sketch aesthetic |
| Embed in docs/PRs | Mermaid MCP | Raw `.mmd` file |
| PoC / mockup / UI | Figma MCP | HTML prototype |
| Data visualisation | HTML (JS/Canvas) | ASCII table |
| Architecture (formal) | Excalidraw (workshops) or Mermaid (docs) | HTML |

### Audience Types

Diagrams support three audiences, indicated by filename suffix:

| Audience | Suffix | Focus | Style |
|----------|--------|-------|-------|
| **Non-Technical** | `_operational` | Business process, user impact | Simple labels, fewer nodes, high contrast |
| **Technical** | `_technical` | System internals, code paths | Full detail, system names, data types |
| **Leadership** | `_leadership` | Business impact, metrics, cost | KPI callouts, strategic framing, timeline |

### When to Include Diagrams (Any Type)

- Complex workflows with 4+ steps
- Multi-system interactions
- Data relationships across 3+ tables
- Decision trees or state transitions
- Architecture requiring spatial understanding

### When to Skip Diagrams

- Simple linear processes
- Single-system operations
- Text descriptions are clearer

### ASCII vs File-Based Decision

Use **ASCII inline** when:
- Diagram has fewer than 10 nodes
- No interactivity needed
- Quick explanation in conversation flow
- Version control / PR description context

Use **file-based** (`/diagram`) when:
- Complex layout ASCII cannot represent clearly (10+ nodes, crossing lines)
- Interactivity adds value (zoom, tooltips, collapsible sections)
- Presentation-quality output needed
- Data visualisation with charts/graphs
- Persistent artefact needed beyond the conversation

## Data Gathering Best Practices

**Database Selection for Investigations:**

Choose the appropriate database based on the type of analysis:

| Tool | Use For |
|------|---------|
| `production database tool` | Investigation/analysis, schema analysis, data distribution, evidence gathering |
| `staging/branch database tool` | Testing code changes on branches, evaluating DB impact, quick fix validation, database schema changes, performance testing |
| `local database tool` | Only when explicitly requested or dev/testing scenarios specified |

**Key Principle:** Production data (via `production database tool` or `staging/branch database tool`) reveals real patterns and customer impact. Choose the tool based on whether you're analyzing existing data or testing changes.

**Always document data sources, queries, and findings in notes for traceability and quality.**
