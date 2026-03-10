# Prompt Supplements Best Practices

NOTE: Written by Claude 🪄

This document provides best practices for writing effective prompt supplements for docdigest. Prompt supplements allow you to add custom instructions to the AI summarization process to enforce brand guidelines, terminology, and style preferences.

## Quick Start

Add a `prompt_supplement` field to your `docdigest_config.json`:

```json
{
  "directory": "docs/",
  "output_file": "static/js/summaries.js",
  "prompt_supplement": [
    "Always use 'DataFlow Pro' as the product name, never just 'DataFlow'",
    "Emphasize enterprise features and scalability when relevant"
  ]
}
```

## Best Practices

### 1. Be Specific and Actionable

**Good:** "Always use 'DataFlow Pro' as the product name, never just 'DataFlow'"
**Bad:** "Use correct product names"
**Why:** Specific instructions eliminate ambiguity and ensure consistent results

### 2. Use Positive Instructions (Do This) Rather Than Negative (Don't Do That)

**Good:** "Use active voice and present tense"
**Bad:** "Don't use passive voice or past tense"
**Why:** Positive instructions are clearer and easier for the AI to follow

### 3. Prioritize Brand and Terminology Consistency

**Good:** "Refer to our solution as 'Enterprise Data Platform' not 'software' or 'tool'"
**Why:** Consistent terminology across all documentation reinforces brand identity

### 4. Keep Instructions Concise

**Good:** "Emphasize security features when discussing data handling"
**Bad:** "When you are writing about any features that involve data, make sure to mention that we have security features and compliance certifications"
**Why:** Concise instructions are more likely to be consistently applied

### 5. Avoid Conflicting Instructions

**Good:** Have clear, non-contradictory instructions
**Bad:** Having both "Keep summaries technical" and "Use simple language for beginners"
**Why:** Conflicting instructions lead to inconsistent output

### 6. Test Incrementally

**Recommendation:** Start with 1-2 critical instructions, then add more after verifying the initial ones work well
**Why:** Easier to identify which instructions are effective or problematic

### 7. Focus on Domain-Specific Requirements

**Examples:** Industry terminology, compliance language, specific use cases
**Good:** "When discussing data processing, mention GDPR compliance capabilities"
**Why:** These are unique to your documentation and can't be covered by the base prompt

## Common Use Cases

### Brand Consistency
```json
"prompt_supplement": [
  "Always use 'DataFlow Pro' as the product name",
  "Refer to our company as 'DataCorp' not 'the company'"
]
```

### Technical Terminology
```json
"prompt_supplement": [
  "Use 'real-time analytics' not 'live analytics'",
  "Refer to data storage as 'data lakes' when discussing large-scale storage"
]
```

### Compliance and Security
```json
"prompt_supplement": [
  "When discussing data processing, mention GDPR compliance capabilities",
  "Emphasize security features for enterprise-grade data handling"
]
```

### Writing Style
```json
"prompt_supplement": [
  "Use active voice and present tense consistently",
  "Emphasize practical benefits for users"
]
```

## Troubleshooting

### Problem: Supplements not being applied
**Solution:** Check that your config file is valid JSON and that the `prompt_supplement` field is properly formatted as an array of strings.

### Problem: Conflicting or unclear results
**Solution:** Review your instructions for conflicts. Try removing some instructions and testing with fewer, clearer directives.

Base prompts:
* [Summarization](./docdigest/summarize.py)
* [Meta descriptions](./docdigest/meta_description.py)

### Problem: Instructions too generic
**Solution:** Be more specific. Instead of "use good writing," specify "use active voice and keep sentences under 15 words."

## Implementation Notes

- Prompt supplements are only applied when using Claude (not in dry-run mode with `--llm none`)
- Supplements are applied to all summaries in a batch
- The feature is fully backward compatible - existing configurations without `prompt_supplement` continue to work unchanged
- If the `prompt_supplement` field is missing or empty, no additional instructions are added to the prompt

## Examples

### Before (without supplements)
Summary: "This guide covers data processing features."

### After (with brand supplement)
Config:
```json
"prompt_supplement": ["Always use 'DataFlow Pro' as the product name"]
```
Summary: "This guide covers DataFlow Pro's data processing features."

### Advanced Example
Config:
```json
"prompt_supplement": [
  "Always use 'DataFlow Pro' as the product name",
  "Emphasize enterprise-grade capabilities",
  "Mention scalability when discussing performance features",
  "Use active voice and present tense"
]
```

Summary: "Explains how DataFlow Pro's enterprise-grade data processing delivers scalable performance for large datasets. Covers real-time analytics capabilities and batch processing options."
