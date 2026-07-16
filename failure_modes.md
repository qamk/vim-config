# Failure-Mode Classification

**Purpose**: A reusable schema for cataloguing the *specific* ways a system fails — failure modes that are more precise than "service X is down", scoped to where they occur, how they fail, and who they affect. This file is the **definitive, project-agnostic schema**. Concrete catalogues live per-project (see "Where things live").

A failure mode is a point in six axes: **Category** (what kind of fault), **Layer** (where in the stack), **Failure-shape** (how it fails — the mechanism), **Coupling** (one service or many), **Impact** (what the user experiences), and **Blast radius** (how far it spreads). Two boolean-ish refinements — `silent` and `status` — round out an entry.

---

## Where things live (three tiers)

| Tier | Owns | Location |
|------|------|----------|
| **Framework** (this file) | The schema + universal vocabulary: categories, failure-shapes, impacts, blast-radius values, the entry shape, the ID convention | `agentic://references/failure_modes` |
| **Project vocabulary** | The project-specific controlled lists: `services`/`known_components`, `known_libraries`, `infra_external`, `failure_layers` | `agentic://projects/<encoded>/architecture.md` (managed by `/init-project`) |
| **Instances** | The actual catalogued modes for a project | `<project>/$NOTES_DIR/failure_modes/catalogue.toml` (+ derived `INDEX.md`) |

The test for "framework vs project": *would this value mean the same thing on a different codebase?* `FS-1 stale-state deadlock` → yes (framework). A specific service name → no (project). A layer's *definition* is universal; a layer's *membership* (which services sit in it) is project-specific.

---

## Categories (the spine)

What *kind* of fault is it? An entry may carry more than one (a single mode is often a Bug *and* a Configuration Gap). The first seven mirror a request-classification taxonomy; the eighth is added because failures routinely originate outside the platform.

| Category | Meaning |
|----------|---------|
| `bug` | A defect in code we own — logic error, missing guard, race, swallowed exception |
| `infrastructure` | Resource/platform-level: exhaustion, eviction, contention, deploy lifecycle, networking we run |
| `configuration-gap` | A setting, flag, limit, or vocabulary that is wrong, drifted, missing, or unwired |
| `instrumentation-gap` | The failure was invisible or misreported — logging/metrics/alerting deficiency |
| `knowledge-gap` | A gap in operator/user understanding contributed (e.g. a testing path that masked the fault) |
| `user-error` | The trigger was a user action against the system working as designed (often terminology/expectation mismatch) |
| `hallucination` | The model asserted unsourced content or an action it never performed |
| `external-integration` | The fault originates outside the platform: customer network/ISP/proxy, a third-party API, a retired provider model |

---

## Layers (where it manifests)

Layers describe *where in the stack* a failure surfaces, cutting across organisational/domain boundaries. **The set of layers is project vocabulary** (`failure_layers` in the project's `architecture.md`) — a project declares its own. Each layer has a short **ID code** used in entry IDs.

A typical layer set for an AI-agent platform, with codes:

| Code | Layer | Scope |
|------|-------|-------|
| `ING` | INGESTION | upload → parse → extract pipeline |
| `SYNC` | SYNC | external data synchronisation |
| `ORCH` | ORCHESTRATION | run lifecycle, retries, streaming/delivery plumbing |
| `INFER` | INFERENCE | model reasoning, tool-calling, generation, agent behaviour |
| `ROUTE` | ROUTING | request classification → workflow/skill selection |
| `AUTH` | AUTH | authentication, authorization, RBAC, SSO |
| `EXT` | EXTERNAL | faults originating outside the platform |
| `OBS` | OBSERVABILITY | instrumentation, logging, metrics gaps |
| `PRES` | PRESENTATION | how output/data is rendered (to user *or* model) |

A project's catalogue declares its own `layer_codes` map in the catalogue header so IDs stay short and stable even as layer *names* are made readable.

---

## Failure-shapes (the reusable mechanisms)

The heart of the system. A failure-shape is the *mechanism pattern* — what actually goes wrong. Shapes are universal (project-agnostic) and are what let one mode span services, categories, and layers. Each is observed across many incidents; cite the shape(s) on every entry.

| ID | Shape | Mechanism |
|----|-------|-----------|
| `FS-1` | **Stale-state deadlock** | A lock/heartbeat/guard is set, the holder dies or hangs, no TTL/reaper releases it → permanent block |
| `FS-2` | **Retry amplification** | A failure triggers a retry that re-enters the same starved or poisoned path, amplifying load or repeating the fault |
| `FS-3` | **Resource-exhaustion eviction** | An unbounded resource (disk, memory, context tokens, connections) → kill/reject → cascade |
| `FS-4` | **Noisy-neighbour contention** | One tenant's load starves a shared resource, harming others; no per-tenant bulkhead |
| `FS-5` | **Async ordering race** | Two async paths with no synchronisation gate; one reads before the other finishes |
| `FS-6` | **Silent failure** | An error is swallowed, a status is mislabelled "success", or a metric under-reports reality |
| `FS-7` | **Contract / version skew** | Client/server or producer/consumer disagree on schema/enum after a partial deploy |
| `FS-8` | **Over-broad fail-closed** | A guard rejects more than intended (all-or-nothing batch, resource-type-blind check) |
| `FS-9` | **Content/format mismatch** | Data labelled or shaped wrong for the downstream consumer |
| `FS-10` | **Run-to-run non-determinism** | Same inputs, different outputs (source selection, generated code, procedural output) |
| `FS-11` | **Fabrication** | The model asserts unsourced content or an action it never performed |
| `FS-12` | **Client-side interception** | A proxy/ISP/secure-web-gateway blocks connectivity before the request reaches the platform |
| `FS-13` | **Provenance loss** | Metadata (source, timestamp, origin) is dropped during a transform/render |
| `FS-14` | **Over-broad fail-open** | A guard grants more than intended when its input is absent, empty, or ambiguous — a missing signal defaults to "permit" instead of "deny" → silent over-exposure. The security-critical mirror of `FS-8`: fail-closed over-denies and screams; fail-open over-permits and whispers (discovered late, often by someone noticing they can see too much) |

New shapes are added here when a mechanism recurs (≥2 independent incidents) and isn't captured by an existing shape.

---

## Impact (what the user experiences)

| Value | Meaning |
|-------|---------|
| `hang` | No response; request stuck indefinitely |
| `slow` | Degraded latency, eventually completes |
| `missing` | A response is delivered but an expected artefact (attachment, file) is silently absent |
| `wrong` | Incorrect or incomplete output |
| `fabricated` | Confidently false content |
| `blocked` | Lockout / access denied / cannot proceed |

## Blast radius (how far it spreads)

| Value | Meaning |
|-------|---------|
| `self` | Only the triggering request/document |
| `user` | All of one user's work |
| `tenant` | Multiple entities within one tenant (e.g. one stuck item blocks others) |
| `cross-tenant` | Spills across tenants via a shared resource |

A blast radius beyond `self` almost always signals **missing isolation** (pairs with FS-3, FS-4).

## `silent` — shape *or* flag

Silence is both a shape (`FS-6`) and a modifier (`silent: true`). Disambiguate with one test: **did the silence change the outcome?**
- **Yes** → the suppression *is* the mechanism → cite `FS-6` as a shape (e.g. a swallowed exception that skips a retry, so the artefact is never delivered).
- **No, it only delayed detection** → the failure happened regardless, but went undetected → set `silent: true` on whatever the real shape was.

## `status`

`open` · `mitigated` (partial/workaround in place) · `resolved`.

---

## Entry schema

The catalogue is a TOML file (read with stdlib `tomllib`, no external deps). Each entry is one `[[modes]]` table:

```toml
[[modes]]
id = "ING-02"                       # <LAYER-CODE>-NN, stable for life
name = '''Zombie-document lockout''' # crisp 3-6 word label (literal string)
aliases = ["Issue D"]               # optional prior/local names
category = ["bug", "infrastructure"] # one or more from Categories
layer = "INGESTION"                 # one value from the project's failure_layers
shape = ["FS-1", "FS-3"]            # one or more failure-shapes
coupling = "single-svc"             # single-svc | cross-svc
services = ["parser"]               # validated against project vocabulary
impact = ["hang"]                   # one or more from Impact
blast_radius = "tenant"             # one value from Blast radius
silent = false                      # detection-only invisibility (see above)
status = "mitigated"                # open | mitigated | resolved
mechanism = '''...'''               # 1-2 sentences: the specific mechanism, not symptoms
occurrences = [                     # observed instances; ref points at the investigation note/report
  { date = 2026-05-21, customers = 5, ref = "2026-05-21/parser_eviction.md" },
]
```

Convention: enums/ids/services use `"..."`; `name` and `mechanism` use `'''...'''` literal strings (so embedded quotes/arrows/apostrophes need no escaping). Omit `customers` when unknown (TOML has no null).

**ID rule**: the `<LAYER-CODE>` prefix is fixed at creation and never changes, even if the entry is re-classified to a different layer later (rename the layer field, keep the ID). This keeps cross-references in notes/reports stable.

---

## Keeping it updated

The per-mode prose (full mechanism, evidence, timeline) lives in **investigation notes**, not here. The catalogue *references* those notes; it does not duplicate them. `catalogue.toml` is the single source of truth; `INDEX.md` and any diagrams are **derived, never hand-edited**.

**Single owner — the `/failure-mode` skill.** All lifecycle operations go through it, so the catalogue has exactly one writer:
- **`init`** — bootstrap the project's vocabulary + catalogue + index (idempotent). Also invoked by `/init-project` as an optional phase.
- **`add` / `update`** — propose-update-before-create: a recurrence appends to a mode's `occurrences`; a genuinely new mode gets a new entry. Validates `services` / `layer` against the project vocabulary, rejecting unknown values (catches typos and drift).
- **`index`** — regenerate `INDEX.md` and validate the whole catalogue.

**`/note` delegates.** When an investigation surfaces a mode, `/note` calls `/failure-mode add` (passing the note's path as the occurrence `ref`), then stamps the returned id(s) into the note's `failure_modes: [<id>, ...]` frontmatter. `/note` never writes the catalogue directly.

**Trigger cadence:** primarily at **roundup time** (roundups already enumerate failure modes — extracting them is one step); secondarily at **investigation close**. Retroactive backfill of `failure_modes:` tags on older notes is deferred.

**Derived outputs:** a stdlib-only build script (`tomllib` + the shared `frontmatter` parser for the vocabulary) reads `catalogue.toml`, validates every entry against the schema and project vocabulary, and regenerates `INDEX.md` (the human-browsable table with rollups). Diagrams are authored from the same catalogue data via `/diagram` (e.g. a layer×service matrix, shape-frequency, or service-coupling view) — not auto-emitted by the build script.
