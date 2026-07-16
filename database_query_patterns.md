# Database Query Patterns

**Purpose**: Database query safety patterns for agents and skills that interact with databases.

**Critical principles**:

1. **Prefer migration files when the question is about schema shape.** Migrations are version-controlled, authoritative, and capture history that a live schema view cannot.
2. **When live data is needed, inspect schema before querying.** Never trust column-name assumptions from memory or documentation.
3. **Bound results before fetching.** Count first, sample with `LIMIT`, produce a script for large datasets.

---

## Source discovery order

When an investigation concerns schema or data, consider sources in this order — authoritative-and-always-available first, optional/project-dependent last.

1. **Migration files in the repo** — `**/migrations/`, `**/alembic/versions/`, `db/migrate/`, `prisma/migrations/`, `schema.sql`, etc. Authoritative for schema shape and evolution. Always present where an app uses migrations.
2. **Documented DB CLI via Bash** — `psql`, `mysql`, `sqlite3`, and equivalents. Usually installed on the developer machine; requires connection details from project config (env, `~/.pgpass`, etc.) or a Cloud SQL proxy.
3. **DB-oriented MCP** — scan available MCP tools for one matching the project's database. Often absent; treat as a nice-to-have, not a baseline assumption.

The patterns below apply once a live-query source has been chosen (steps 2 or 3). For schema-only questions, step 1 (migrations) is often enough.

---

## Terminology

Throughout this document:

- **`target_table`**, **`primary_table`**, **`foreign_table`** — generic placeholders for whatever table the current query concerns.
- **`tenant_id`** is used in examples as the project's **scope / tenant / workspace identifier column**. Real projects use various names: `tenant_id`, `org_id`, `workspace_id`, `account_id`, `scope_id`, etc. Substitute the actual column from the target schema — don't assume.

---

## Schema-First Query Pattern (MANDATORY)

**Problem**: Queries fail due to incorrect assumptions about column names (camelCase vs snake_case), data types, or table structure.

**Solution**: For live queries, check `information_schema` FIRST to get the actual schema, then construct the query. For schema questions, read the migration files — they describe the intended shape and its history.

### Step 0: Schema inspection (required before any live query)

```sql
-- Column names, types, nullable status
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'target_table'
ORDER BY ordinal_position;

-- Primary key
SELECT constraint_name, column_name
FROM information_schema.key_column_usage
WHERE table_name = 'target_table'
  AND constraint_name LIKE '%_pkey';

-- Foreign keys
SELECT
    tc.constraint_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_name = 'target_table'
  AND tc.constraint_type = 'FOREIGN KEY';
```

### Step 1: Construct the query using verified schema

**Example workflow:**

```
1. User asks: "Find records for tenant X in the target table."
2. Agent: read migration for the table (authoritative) OR run the information_schema
   query above on a live connection.
3. Agent: confirm the scope column is `tenant_id` (not `tenantId`, not `tenant`),
   and that it's non-nullable.
4. Agent: write the query: SELECT * FROM target_table WHERE tenant_id = 'xxx'
```

**Benefits:**

- Eliminates retry cycles from incorrect column names.
- Confirms data types before casting or comparison.
- Reveals nullable columns that need special handling.
- Surfaces foreign key relationships for joins.

---

## Query Result Size Management

**Problem**: Large query results (25K+ tokens of output) exhaust the context window, making investigation impossible.

**Solution**: Count first, sample with `LIMIT`, produce a reusable script for anything larger than the inline threshold.

### Step-by-step pattern

```sql
-- STEP 1: Count total results FIRST
SELECT COUNT(*) AS total_count
FROM target_table
WHERE condition;
-- Result: 1,234 rows (hypothetical)

-- STEP 2: Decision based on count
-- If count ≤ 20: safe to run the full query inline.
-- If count > 20: use LIMIT for sampling; produce a script for the full extract.

-- STEP 3a: Small result set (count ≤ 20)
SELECT *
FROM target_table
WHERE condition;

-- STEP 3b: Large result set (count > 20)
-- Run LIMIT query for pattern analysis
SELECT *
FROM target_table
WHERE condition
LIMIT 20;

-- Then create a SQL script WITHOUT LIMIT for the user to run. Conventional
-- location: $SCRIPTS_DIR/sql/<descriptive>.sql, producing output under
-- $DATA_DIR/<descriptive>.csv when executed.
```

### Decision framework

| Row count | Action | Rationale |
|-----------|--------|-----------|
| ≤ 20 | Run full query inline | Safe for context; full analysis possible |
| 21–100 | `LIMIT 20` sample, plus a script | Sample sufficient for patterns; script for full data |
| > 100 | `LIMIT 20` sample, plus a script | Must go through user-run script → CSV |

### Critical rules

1. **Any query that could return > 1 row MUST count first.**
2. **If COUNT > 20, LIMIT the inline query.**
3. **Produce a SQL script (without LIMIT) for the user to run and produce CSV.**
4. **Never run the full inline query if count > 20** — this exhausts context.

### Example

```sql
-- STEP 1: Count first (suppose this returns 123 duplicate rows)
SELECT COUNT(*)
FROM duplicate_candidates
WHERE tenant_id = 'xxx';
-- Result: 123

-- STEP 2: Sample with LIMIT for pattern analysis
SELECT *
FROM duplicate_candidates
WHERE tenant_id = 'xxx'
LIMIT 20;

-- STEP 3: Script (no LIMIT) for the user to run. Save as
-- $SCRIPTS_DIR/sql/duplicate_candidates_report.sql and produce the CSV at
-- $DATA_DIR/duplicate_candidates_report.csv (123 rows) when the user runs it.
```

---

## Data Isolation Pattern

**Problem**: Queries that span tenants risk data leakage, accidental cross-tenant reads, and performance issues on large datasets.

**Solution**: Always scope queries to the project's tenant/scope column unless the query is explicitly and justifiably system-wide.

### Tenant-scoped query (default)

```sql
-- Always include the project's scope column in WHERE
SELECT *
FROM target_table
WHERE tenant_id = 'tenant-value'
  AND other_conditions;
```

### System-wide query (requires justification)

```sql
-- Only when explicitly analysing cross-tenant patterns.
-- Must include a comment explaining why cross-tenant is needed.
-- Must use LIMIT aggressively.
SELECT tenant_id, COUNT(*) AS count
FROM target_table
WHERE condition
GROUP BY tenant_id
LIMIT 50;   -- stricter limit for cross-tenant queries
```

### Validation checklist

Before executing any query:

- [ ] Does the query include the project's scope/tenant filter?
- [ ] If cross-tenant, is it justified and aggressive with `LIMIT`?
- [ ] Have I checked schema (migration or `information_schema`) first?
- [ ] Have I counted rows before fetching?
- [ ] Will results fit in context (≤ 20 rows or `LIMIT` applied)?

---

## Multi-Table Investigation Pattern

**Problem**: Need to understand relationships between tables before querying.

**Solution**: Map foreign keys first; then use `JOIN` / `LEFT JOIN` to detect orphans and count impact.

### Step 1: Discover foreign key relationships

```sql
-- Foreign keys FROM this table
SELECT
    tc.constraint_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_name = 'primary_table'
  AND tc.constraint_type = 'FOREIGN KEY';

-- Foreign keys TO this table
SELECT
    tc.table_name AS referencing_table,
    kcu.column_name AS referencing_column,
    tc.constraint_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE ccu.table_name = 'target_table'
  AND tc.constraint_type = 'FOREIGN KEY';
```

### Step 2: Detect orphaned records

```sql
-- Records in primary_table without a matching foreign_table row
SELECT pt.id, pt.foreign_key_column
FROM primary_table pt
LEFT JOIN foreign_table ft ON pt.foreign_key_column = ft.id
WHERE ft.id IS NULL
  AND pt.tenant_id = 'tenant-value'
LIMIT 20;
```

### Step 3: Count impact before fixes

```sql
-- Always count affected records before planning fixes
SELECT COUNT(*) AS orphaned_count
FROM primary_table pt
LEFT JOIN foreign_table ft ON pt.foreign_key_column = ft.id
WHERE ft.id IS NULL
  AND pt.tenant_id = 'tenant-value';
```

---

## Index and Constraint Discovery

**When needed**: before creating migrations, analysing slow queries, or understanding table relationships.

```sql
-- All indexes on a table (Postgres)
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'target_table';

-- All constraints (PK, FK, UNIQUE, CHECK)
SELECT tc.constraint_name, tc.constraint_type, kcu.column_name
FROM information_schema.table_constraints AS tc
LEFT JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
WHERE tc.table_name = 'target_table'
ORDER BY tc.constraint_type, tc.constraint_name;
```

---

## Query Performance Considerations

### Use `EXPLAIN` for complex queries

```sql
-- Before running an expensive query, check the execution plan
EXPLAIN ANALYZE
SELECT *
FROM large_table
WHERE complex_condition
LIMIT 20;
```

### Avoid `SELECT *` on wide tables

```sql
-- ❌ BAD — fetches all columns, wastes context
SELECT * FROM large_table WHERE condition LIMIT 20;

-- ✅ GOOD — fetch only needed columns
SELECT id, name, status, created_at
FROM large_table
WHERE condition
LIMIT 20;
```

---

## Common Mistakes to Avoid

1. **Assuming column names without checking schema**
   - ❌ `SELECT userId FROM table` (fails if column is actually `user_id`)
   - ✅ Check migration or `information_schema` first; use the confirmed name.

2. **Running unbounded queries**
   - ❌ `SELECT * FROM large_table WHERE condition` (could return 10K rows)
   - ✅ `SELECT COUNT(*)` first; `LIMIT 20` for sampling; script for the rest.

3. **Forgetting the tenant-scope filter**
   - ❌ `SELECT * FROM table WHERE id = 123` (could return another tenant's data)
   - ✅ `SELECT * FROM table WHERE id = 123 AND tenant_id = 'xxx'`

4. **Skipping foreign-key discovery before multi-table operations**
   - ❌ Updating parent rows without checking dependent tables
   - ✅ Query `information_schema` for FKs; verify cascade behaviour.

5. **Using `JOIN` without understanding the relationship**
   - ❌ Guessing join columns
   - ✅ Check `information_schema.table_constraints` for actual FK columns.

---

## Integration with Agent Workflows

**For agents**: reference this file when your prompt includes database operations.

**Agent invocation pattern**:

```markdown
Prompt: "[Task requiring database queries]

Source discovery (in order):
- Migration files in the repo (schema shape, history)
- DB CLI (psql / mysql / sqlite3) for live queries if connection details are available
- DB-oriented MCP if one exists

Critical: follow agentic://references/database_query_patterns
- STEP 0: Check schema (migration or information_schema) before any live query
- Use the COUNT → LIMIT → script pattern for multi-row results
- Scope to the project's tenant column unless system-wide is justified

[Additional task context]"
```

**Consumers that MUST reference this file:**

- `/investigate` skill — when the investigation gathers schema or data evidence
- `data-integrity-validator` — always
- `grounding-auditor` — for schema / data verification

---

## Quick Reference

**Before any database query:**

1. ✅ Schema: migration file first, then `information_schema` if querying live.
2. ✅ COUNT results before fetching.
3. ✅ `LIMIT 20` if COUNT > 20; script the full extract separately.
4. ✅ Include the project's tenant-scope filter unless system-wide is justified.
5. ✅ Create a SQL script for the user if the extract is large.

**Schema inspection query template:**

```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'your_table'
ORDER BY ordinal_position;
```

**Result size decision:**

- COUNT ≤ 20: run the full query inline.
- COUNT > 20: `LIMIT 20` + separate script.
