## Command reference

Use one of the following commands to run `docdigest`:

```
# Use config docdigest_config.json
docdigest

# Specify custom config
docdigest --config docdigest_custom.json

# Use dry run mode to ensure processing goes as expected
docdigest --llm none

# Estimate costs with Claude
docdigest --llm claude --estimate-cost

# Summarize with Claude
docdigest --llm claude

# Run summarization in automation mode
docdigest --automation --llm claude

# Generate meta descriptions, printed to stdout
docdigest --generate meta-descriptions

# Generate meta descriptions, and post suggestions to GitHub PR
docdigest --generate meta-descriptions --automation
```
