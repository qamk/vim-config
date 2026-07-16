# Path Variables & Project Configuration

Central mapping of abstract variable references to concrete locations. To make these instructions project-agnostic, **update only this file** when switching projects.

All other `~/.claude/*.md` files and `agentic://agents/*.md` files use these variables.

## Dynamic Resolution

Projects can be detected automatically from the current working directory:

1. **List known projects**: `ls -d agentic://projects/*/` — each directory name encodes the project path (e.g. `-Users-username-myorg-code-repo`)
2. **Decode the path**: replace leading `-` with `/`, then all `-` with `/` (the encoding replaces `/` with `-`)
3. **Match against `cwd`**: the current working directory will be within one of these decoded paths
4. **Derive `$PROJECT_ROOT`**: take the first directory component after `~/` from the matched path (e.g. `~/myorg/code/repo` → `~/myorg`). This is the project root — notes, reports, data, and scripts live here, outside any git repo.
5. **Derive `$CODE_DIR`**: the full decoded path is the git-tracked codebase (e.g. `~/myorg/code/repo`). Never put generated artifacts (notes, reports) inside this directory.

## Project Identity

| Variable | Description | Current Value |
|----------|-------------|---------------|
| `$PROJECT` | Project identifier used in paths | `m5` |

## Directory Structure

| Variable | Description | Current Path |
|----------|-------------|--------------|
| `$PROJECT_ROOT` | Root directory for project artifacts (first dir after ~) | `~/fifthdimensionai` |
| `$CODE_DIR` | Project codebase root (the git repo) | `$PROJECT_ROOT/code/m5` |
| `$NOTES_DIR` | Working investigation notes | `$PROJECT_ROOT/working_notes` |
| `$REPORTS_DIR` | Generated reports output | `$PROJECT_ROOT/reports/generated` |
| `$PLAYBOOKS_DIR` | Scenario-keyed playbooks | `$PROJECT_ROOT/playbooks` |
| `$SCRIPTS_DIR` | Scripts directory (SQL, utilities, etc.) | `$PROJECT_ROOT/code/scripts` |
| `$DATA_DIR` | Data files (CSV exports, query results) | `$PROJECT_ROOT/data` |
| `$MEMORY_DIR` | Claude memory files for this project | `agentic://projects/-Users-qamk-fifthdimensionai-code-m5/memory` |
| `$DIAGRAMS_DIR` | Generated diagram outputs | `$PROJECT_ROOT/diagrams` |
| `$DIAGRAM_THEME` | Project-specific diagram theme overrides | `agentic://projects/-Users-qamk-fifthdimensionai-code-m5/diagram-theme.md` |

## Directory Structures

### Working Notes (`$NOTES_DIR`)

```
$NOTES_DIR/
├── YYYY-MM-DD/
│   ├── ticket_description.md
│   ├── feature_investigation.md
│   └── architecture_analysis.md
└── taxonomy.json
```

### Generated Reports (`$REPORTS_DIR`)

```
$REPORTS_DIR/
├── problem_solution_reports/
│   ├── operational/
│   ├── technical_junior_mid/
│   ├── technical_senior_plus/
│   └── leadership/
├── analysis_reports/
│   ├── leadership/
│   └── technical/
├── outline_reports/
│   ├── operational/
│   ├── general_onboarding/
│   └── technical_onboarding/
├── feature_release_reports/
│   ├── operational/
│   ├── leadership/
│   └── technical/
├── post_mortem_reports/
├── roundup_reports/
└── handoff_reports/
    ├── tier_2/
    └── tier_3/
```

### Scripts (`$SCRIPTS_DIR`)

```
$SCRIPTS_DIR/
├── sql/
│   ├── {company_name}/    # Company-specific scripts
│   ├── _snippets/         # Reusable templates
│   └── general/           # Cross-company utilities
└── ...                    # Other script types as needed
```

### Data Files (`$DATA_DIR`)

```
$DATA_DIR/
└── {company_name}/        # Per-company query results and exports
```

### Diagrams (`$DIAGRAMS_DIR`)

```
$DIAGRAMS_DIR/
├── {topic}/
│   ├── flow-{descriptive-name}_operational.html
│   ├── flow-{descriptive-name}_technical.html
│   ├── architecture-{descriptive-name}_leadership.html
│   └── sequence-{descriptive-name}_technical.mmd
└── {another-topic}/
    └── ...
```

**Naming convention:** `{type}-{descriptive-name}_{audience}.{ext}`
- **Type prefixes:** `flow-`, `architecture-`, `investigation-`, `data-`, `sequence-`, `state-`, `dependency-`, `decision-`, `timeline-`, `comparison-`, `map-`
- **Audience suffixes:** `_operational`, `_technical`, `_leadership`
- **Extensions:** `.html` (default), `.mmd` (Mermaid), `.excalidraw`, `.txt` (ASCII to file, rare)
