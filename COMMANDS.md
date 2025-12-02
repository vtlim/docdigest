## Command reference

Use one of the following commands to run `docdigest`:

```
# Use config docdigest_config.json
docdigest

# Specify custom config
docdigest --config docdigest_custom.json

# Use debug mode to ensure processing goes as expected
docdigest --model debug

# Estimate costs with Claude
docdigest --model claude --dry-run

# Summarize with Claude
docdigest --model claude

# Run summarization in automation mode
docdigest --automation --model claude

# Generate meta descriptions, printed to stdout
docdigest --meta

# Generate meta descriptions, and post suggestions to GitHub PR
docdigest --meta --automation
```
