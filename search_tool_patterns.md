# Search Tool Patterns

**Purpose**: Optimized search tool usage for efficient code and content discovery.

**Critical Principle**: **Prefer ripgrep (`rg`) over `grep` for speed and smart defaults.**

---

## Tool Selection

**In Claude Code Sessions**: ALWAYS use Grep tool (uses ripgrep internally with optimized permissions)

**In Standalone Scripts**: Use `rg` CLI directly

**Edge Cases Only**: Use traditional `grep` for fixed strings (`-F`), binary files (`-a`), or POSIX compatibility

---

## Claude Code Grep Tool Patterns

### Basic Usage

```javascript
// Find files containing pattern
Grep({ pattern: "handleInvoiceSync", output_mode: "files_with_matches" })

// Search with context and line numbers
Grep({ pattern: "class Invoice", output_mode: "content", "-n": true, "-C": 3 })

// Case-insensitive
Grep({ pattern: "invoice", "-i": true, output_mode: "content" })

// Type-specific (faster)
Grep({ pattern: "handleInvoiceSync", type: "ts", output_mode: "files_with_matches" })

// Glob pattern
Grep({ pattern: "the project API framework", glob: "packages/backend/**/*.ts", output_mode: "files_with_matches" })

// Count matches
Grep({ pattern: "TODO:", output_mode: "count" })

// Multiline search
Grep({ pattern: "interface Invoice\\{[\\s\\S]*?\\}", multiline: true, output_mode: "content" })
```

---

## Ripgrep CLI (For Scripts Only)

```bash
# List files with pattern
rg -l "handleInvoiceSync"

# Type-specific
rg -l --type ts "handleInvoiceSync"

# With context
rg -C 3 "handleInvoiceSync"

# Case-insensitive
rg -i "invoice"

# Exclude patterns
rg "invoice" --glob '!*.test.ts'

# Count matches
rg -c "TODO:"

# Specific directory
rg -l "pattern" packages/backend/
```

---

## Performance Tips

1. **Use type filtering**: `type: "ts"` is much faster than searching all files
2. **Use specific paths**: `path: "packages/backend/src"` limits scope
3. **Use head_limit**: `head_limit: 20` stops after 20 results
4. **Literal strings faster than regex**: Use simple strings when possible

---

## Common Mistakes

❌ Using Bash rg/grep in Claude Code sessions:
```javascript
Bash({ command: "rg -l pattern" })  // BAD
```

✅ Use Grep tool instead:
```javascript
Grep({ pattern: "pattern", output_mode: "files_with_matches" })  // GOOD
```

---

## Quick Reference

| Task | Claude Code Grep Tool | Bash rg (Scripts) |
|------|----------------------|-------------------|
| Find files | `Grep({ pattern: "X", output_mode: "files_with_matches" })` | `rg -l "X"` |
| With context | `Grep({ pattern: "X", output_mode: "content", "-C": 3 })` | `rg -C 3 "X"` |
| Type-specific | `Grep({ pattern: "X", type: "ts" })` | `rg --type ts "X"` |
| Case-insensitive | `Grep({ pattern: "X", "-i": true })` | `rg -i "X"` |
