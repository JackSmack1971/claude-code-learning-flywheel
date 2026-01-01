---
name: LSP-First Navigation
version: 1.0.0
category: code-navigation
last_verified: 2026-01-01
verification:
  test_script: "tests/skills/test_lsp_navigation.py"
  command: "python3 tests/skills/test_lsp_navigation.py"
  frequency: "on-change"
---

# LSP-First Navigation

## Directive

Use Language Server Protocol (LSP) tools for code navigation. Avoid grep for symbol lookup.

## Usage

```bash
# Find definition of a symbol
cclsp definition <symbol>

# Find all references to a symbol
cclsp references <symbol>

# Get hover information
cclsp hover <file>:<line>:<col>
```

## Rationale

- **Precision**: LSP understands syntax and semantics
- **Performance**: O(1) lookup vs O(N) grep scan
- **Token Efficiency**: Returns exact location, not file dumps

## Negative Knowledge

| Attempt | Failure | Cost | Fix |
|---------|---------|------|-----|
| Used `grep -r "functionName"` to find definition | Returned 500+ matches including comments, strings, logs | 15k tokens wasted | Use `cclsp definition functionName` for precise lookup |
| Ran `rg "class Foo"` across monorepo | Timed out after 30s, crashed terminal | 2 minutes lost | Use `cclsp definition Foo` - instant results |

## Dependencies

- LSP server running (`cclsp` binary available)
- Indexed codebase
