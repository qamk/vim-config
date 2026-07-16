# Agentic Configuration Compiler

Date: 2026-07-15
Status: Core compiler implemented; Claude canonical import completed; no target installed

## Objective

Create a neutral, agent-independent configuration source at `~/.agentic-config`
that can deterministically compile and copy configuration into Claude, Codex,
Gemini, evaluation harnesses, and future agent systems.

The system must use copy semantics only. It must never move, delete, rename, or
symlink source configuration. Existing `~/.claude`, `~/.codex`, and other agent
directories must remain independently usable after generation.

## Architecture Decision

Use `~/.agentic-config` as the canonical source, with physical generated copies
installed into each target's native directories:

```text
~/.agentic-config
        |
        +-- compile claude --> ~/.claude/...
        +-- compile codex  --> ~/.codex/... and ~/.agents/skills/...
        +-- compile gemini --> ~/.gemini/...
        +-- compile harness --> target-specific isolated tree
```

Targets must not depend on `~/.agentic-config` at runtime. If the canonical
directory is missing, existing generated target configurations must continue
working; only regeneration and updates should be unavailable.

## Canonical Reference Syntax

There are three distinct reference types.

### Managed resources

Use stable logical identifiers for files owned by the canonical configuration:

```text
agentic://reports/modifiers
agentic://schemas/artefact-frontmatter
agentic://scripts/lint-report
agentic://skills/diagram/references/design-tokens
agentic://projects/current/architecture
```

The compiler resolves these identifiers through a resource manifest and renders
target-native physical paths. Canonical instructions should not expose target
directory layouts such as `~/.claude/reports/...`.

### External or contextual values

Use namespaced placeholders:

```text
{{ target.config_dir }}
{{ target.skills_dir }}
{{ user.notes_dir }}
{{ project.root }}
{{ runtime.current_branch }}
{{ secret.slack_token }}
```

Namespaces define the resolver:

- `target.*`: target adapter
- `user.*`: user values file
- `project.*`: project profile or runtime project resolver
- `runtime.*`: intentionally deferred to the shell or agent
- `secret.*`: secret reference only; never copy secret values

### Shell environment variables

Ordinary `$VARIABLE` and `${VARIABLE}` expressions retain shell semantics and
must not be treated as compiler substitutions. For example:

```bash
curl -H "Authorization: Bearer $SLACK_TOKEN" ...
```

Use `\agentic://...` and `\{{ ... }}` when documentation needs to show the
literal compiler syntax.

## Target Feature Contract

Every target definition must explicitly account for every canonical component.
Feature states are:

- `native`: copied in a directly supported format
- `transformed`: converted to a target-specific format
- `emulated`: represented through a different target capability
- `unsupported`: target cannot provide the feature
- `disabled`: intentionally excluded by configuration
- `unmapped`: target definition forgot the component; this is an error

Example:

```toml
[target]
id = "codex"
adapter = "codex"
schema_version = 1

[features.instructions]
status = "native"
destination = "~/.codex/AGENTS.md"
format = "markdown"

[features.skills]
status = "native"
destination = "~/.agents/skills"
format = "agent-skills"

[features.subagents]
status = "transformed"
destination = "~/.codex/agents"
source_format = "canonical-agent"
target_format = "codex-toml"

[features.hooks]
status = "transformed"
destination = "~/.codex/hooks"
manifest = "~/.codex/hooks.json"

[features.resources]
status = "copied"
destination = "~/.codex/agentic"
```

A harness without hooks must state that explicitly:

```toml
[features.hooks]
status = "unsupported"
policy = "warn"
reason = "This harness does not expose lifecycle hook events."
```

Default policy:

```text
native/transformed  continue
emulated            warn
unsupported         warn, unless component is required
disabled            report
unmapped            fail
```

Build output must include human-readable and JSON compatibility reports listing
mapped, transformed, emulated, unsupported, disabled, and unmapped features.

## Compiler Behavior

Treat the tool as a small configuration compiler with separate phases:

```text
canonical configuration + target definition + values
                         |
                         v
                  validated build tree
                         |
                         v
                explicit copy installation
```

Planned commands:

```bash
agentic-config import claude --dry-run
agentic-config import claude --apply
agentic-config build codex
agentic-config validate <build-tree>
agentic-config diff codex
agentic-config install codex
agentic-config sync codex
agentic-config status codex
agentic-config doctor codex
```

`sync` may compose build, validate, diff, and install. The individual commands
must remain available for testing and diagnosis.

The compiler should use a strict scanner rather than a general expression
template engine. Regex is sufficient for the agreed syntax. Internally, parsed
references should become typed objects such as:

```python
Reference(kind="resource", key="reports/modifiers")
Reference(kind="user", key="notes_dir")
Reference(kind="project", key="root")
```

Required unresolved compile-time values must fail before installation.
Explicitly late-bound values may remain unresolved and must be reported.

## Diagnostics

Normal status and summaries go to stdout. Warnings and errors go to stderr.
Support `--format json` for automation.

Suggested exit codes:

- `0`: complete and valid
- `1`: validation or build failure
- `2`: unresolved required values
- `3`: target capability mismatch
- `4`: destination drift or ownership conflict

The tool must report ambiguous legacy references rather than guessing. Example:

```text
AMBIGUOUS skills/report/SKILL.md:82
  Found: $REPORTS_DIR
  Could mean:
    {{ user.reports_dir }}
    shell environment variable $REPORTS_DIR
```

## Installation Safety

Installation must:

1. Render into a staging directory.
2. Validate all rendered files and references.
3. Stop on unresolved required values or unmapped features.
4. Compare the build with the live destination.
5. Detect manually modified generated files.
6. Back up files owned by the generator before replacement.
7. Copy files atomically where possible.
8. Leave all unknown destination files untouched.
9. Write the generation manifest last.

Generated files should identify their source and tell maintainers to edit the
canonical version. A manifest must record target, generation time, source
version, destination files, and SHA-256 hashes.

The tool must never generate or overwrite an entire target-native configuration
file when only a fragment is owned. For example, Codex model and TUI preferences
in `~/.codex/config.toml` should remain user-owned; generated hooks, agents,
skills, resources, and rules should use separate files or carefully delimited
owned fragments.

## Claude Importer

Importing from `~/.claude` is part of the required ingestion path, not scope
creep. Implement it as a read-only source adapter:

```bash
agentic-config import claude --source ~/.claude --dry-run
agentic-config import claude --source ~/.claude --apply
```

The importer must only copy authored configuration. It must not import runtime
state such as authentication, sessions, transcripts, tasks, caches, locks,
telemetry, history, file history, backups, daemon state, or marketplace caches.

Known portable inputs currently identified in `~/.claude`:

- `CLAUDE.md` and its authored reference Markdown files
- `skills/`
- `agents/`
- `hooks/`
- `scripts/`, excluding caches and virtual environments
- `reports/`
- `schemas/`
- `adapters/`
- authored per-project files such as `architecture.md`, `project_terms.txt`,
  `publishing_targets.md`, and `message_targets.md`
- selected declarations from `settings.json`, especially hooks and permissions

Do not copy the current large `plugins/` cache or installed marketplace state.
Custom plugins require separate manifest conversion and should initially be
reported as deferred. MCP credentials and authentication must never be copied;
targets should be reconfigured and reauthenticated separately.

The importer can mechanically normalize known Markdown references:

```text
~/.claude/reports/modifiers.md
    -> agentic://reports/modifiers

~/.claude/schemas/artefact_frontmatter.md
    -> agentic://schemas/artefact-frontmatter
```

Do not blindly rewrite paths inside Python, JavaScript, or shell source. Copy
those files unchanged, scan for hard-coded `~/.claude` references, and emit
repair diagnostics. Markdown shell snippets also require care: managed file
paths may become resource references, but real shell variables must remain
unchanged.

## Proposed Canonical Layout

```text
~/.agentic-config/
|-- README.md
|-- manifest.toml
|-- core/
|-- skills/
|-- agents/
|-- hooks/
|-- resources/
|   |-- adapters/
|   |-- reports/
|   |-- schemas/
|   `-- scripts/
|-- projects/
|-- targets/
|   |-- claude.toml
|   |-- codex.toml
|   `-- <future-target>.toml
|-- transforms/
|-- values/
|-- bin/
|-- tests/
|-- notes/
`-- build/
```

Build products and import reports should be excluded from source control if the
canonical directory is managed as a repository.

## Current Source Observations

The existing Claude configuration contains approximately:

- 988 KiB of user skills
- 124 KiB of custom agents
- 12 KiB of hooks
- 76 KiB of helper scripts
- 72 MiB of plugin data, mostly unsuitable for direct copying
- 262 MiB of project data, mostly runtime history

Only four authored M5 project files were identified as obvious canonical input:
`architecture.md`, `project_terms.txt`, `message_targets.md`, and
`publishing_targets.md`.

Current Claude instructions contain Claude-specific imports, tool names, model
names, and subagent invocation syntax. These require target transformations.
Codex personal skills belong in `~/.agents/skills`, personal custom agents in
`~/.codex/agents`, global guidance in `~/.codex/AGENTS.md`, and hooks in
`~/.codex/hooks.json` or Codex configuration layers.

## Optional Extension: Notes and Produced Artifacts

Content migration is intentionally outside the initial compiler milestone.
Configuration resources and user-produced artifacts have different ownership,
lifecycle, mutability, size, privacy, and duplication concerns. The first
implementation should therefore port agent configuration and selected project
metadata only.

A later content subsystem could optionally handle specific plans, investigation
notes, reports, diagrams, and other artifacts. It should remain opt-in and use
an explicit source path or configured collection rather than scanning all agent
runtime state.

Potential content modes:

- `reference`: record an existing external path without copying it
- `snapshot`: copy stable content into canonical storage and optionally into
  generated targets as read-only reference material
- `workspace`: copy living content once into neutral shared storage so
  multiple agents can read and update the same artifact set

Logical content identifiers should be distinct from configuration resources:

```text
agentic://reports/modifiers       # configuration template
content://completed-reports       # user-produced artifacts
content://working-notes           # living shared content
```

An optional collection might be declared as:

```toml
[content.working-notes]
mode = "workspace"
source = "~/fifthdimensionai/working_notes"
destination = "~/.agentic-config/content/working-notes"
writable = true

[content.completed-reports]
mode = "snapshot"
source = "~/fifthdimensionai/reports/generated"
destination = "~/.agentic-config/content/reports"
```

Any future content importer should default to dry-run, preserve relative paths,
timestamps and frontmatter, record hashes and source paths, detect duplicates
and drift, warn about absolute vendor-specific references, and never alter or
delete source content. It must continue to exclude authentication, caches,
session transcripts, history, telemetry, and other runtime state by default.

This extension may not be worthwhile unless there is a demonstrated need to
move or share artifacts between agents. Do not let it delay the core canonical
configuration compiler.

## Resume Point

The core implementation and a canonical import from `~/.claude` now exist in
`~/.agentic-config`. The import contains 124 allowlisted authored files,
including instructions, skills, agent definitions, hooks, scripts, reports,
schemas, adapters, selected project notes, and non-secret settings. Runtime
state, credentials, histories, caches, transcripts, backups, telemetry, and
plugin caches were excluded. `~/.claude` and `~/.codex` were not modified.

Claude and Codex builds validate and are staged below `build/`; neither build
has been installed into a live harness directory. The CLI provides import,
validate, build, status, diff, install, sync, and doctor commands. Import and
install are dry-run by default, require `--apply` to copy, preflight conflicts
before copying, and never move, delete, or symlink source files.

The remaining portability work is explicit rather than blocking:

1. Review and replace Claude-specific paths in the executable scripts reported
   by `agentic-config doctor codex`.
2. Review Codex hook matchers and payload compatibility before installing them.
3. Decide whether custom plugins merit a separate authored-plugin port; caches
   and marketplace state should remain excluded.
4. Treat the optional artifact/content importer described above as deferred
   until a concrete cross-agent use case justifies it.
