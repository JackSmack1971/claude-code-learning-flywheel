# Pattern: Zero-Context Script Execution

## Context

When an agent or automated system needs to perform complex, deterministic tasks (e.g., validation, linting, data migration) within a multi-agent or high-context environment.

## Problem

1. **Instruction Budget**: Moving complex logic into LLM prompts consumes the context window and increases the risk of "Instruction Drift."
2. **Determinism**: Agents may introduce non-deterministic errors when executing multi-step logic described in natural language.
3. **Reproducibility**: Logic contained only in an agent's history is difficult for other agents or CI/CD pipelines to reuse.

## Solution

Offload logic to standalone, version-controlled scripts (Python/Bash) that operate independently of the agent's session context.

### Structural Skeleton

```python
#!/usr/bin/env python3
"""
Zero-Context Script Template
Does one thing well, requires no session state, and returns structured output.
"""
import sys
from pathlib import Path

def main():
    # 1. Use relative path resolution or environment variables
    root_dir = Path(__file__).parent.parent
    
    # 2. Perform deterministic logic
    # ...
    
    # 3. Return standards-compliant exit codes
    if success:
        print("✅ Success message")
        sys.exit(0)
    else:
        print("❌ Detailed error for agent to parse")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## Gotchas

- **Path Sensitivity**: Hardcoding absolute paths. Always use `Path(__file__)` or pass paths as arguments.
- **Silent Failures**: Not using non-zero exit codes. Agents rely on exit codes to detect success/failure.
- **Context Bleed**: Attempting to read the agent's recent history from within the script. Keep the script "blind" to the session for maximum reliability.
