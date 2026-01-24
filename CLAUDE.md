# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`docdigest` is a Python package that creates AI-powered summaries for Markdown-based documentation. It's designed for Docusaurus sites and can be run manually or automated with CI tools like GitHub Actions.

## Development Commands

### Installation
```bash
# Install dependencies
pip install markdown-analysis anthropic

# Install the package in development mode
pip install -e .
```

### Running docdigest
```bash
# Dry run mode (no API calls, for testing)
docdigest --llm none

# Estimate costs before running
docdigest --llm claude --estimate-cost

# Generate summaries with Claude
docdigest --llm claude

# Generate meta descriptions
docdigest --meta

# Run in automation mode (for CI/CD)
docdigest --automation --llm claude
```

### Testing
Currently no test suite is configured. When adding tests, consider using pytest with the existing Python 3.13 requirement.

## Architecture

### Core Modules

1. **main.py**: Entry point, CLI argument parsing, orchestrates the workflow
2. **parse_docs.py**: Markdown parsing using mrkdwn_analysis, tracks git changes
3. **summarize.py**: AI summarization with Claude Sonnet 4.5, formats as JavaScript modules
4. **import_results.py**: Updates Markdown files with summary imports and components
5. **commitify.py**: Commits changes individually for easy reversion
6. **meta_description.py**: Generates SEO meta descriptions
7. **git_utils.py**: Git operations (change detection, commits, branches)
8. **file_utils.py**: File operations, exclusion logic, ID generation
9. **config.py**: Configuration file handling

### Workflow

1. Parse Markdown files from configured directory
2. Check for changed files since last commit (if configured)
3. Generate summaries using Claude API
4. Write summaries to JavaScript module (summaries.js)
5. Update Markdown files with import statements
6. Commit changes individually (optional)

### Key Design Decisions

- **JavaScript Output**: Summaries are exported as a JavaScript module for Docusaurus integration
- **Git-based Change Detection**: Only processes files changed since a configured commit hash
- **Individual Commits**: Each summary change is committed separately for granular reversion
- **Variable Naming**: Summary variables are named based on file paths (e.g., `tutorial_basics_create_a_document`)
- **Automation Mode**: Creates `bot-summaries` branch and PR automatically

## Configuration

Configuration is in `docdigest_config.json`:
- `directory`: Source Markdown files location
- `output_file`: JavaScript output file path
- `summary_template`: Template for summary component
- `exclude`: Optional exclusion patterns (directories, files, patterns)
- `commit`: Git commit hash for change detection (auto-updated)

## Environment Variables

- `ANTHROPIC_API_KEY`: Required for Claude API access
- GitHub Actions environment variables (for automation mode)

## GitHub Actions

Two workflows are configured:
- **ai-summaries.yml**: Runs weekly or on-demand to generate summaries
- **ai-meta-descriptions.yml**: Generates meta descriptions for PR changes

## Dependencies

- Python 3.13+
- markdown-analysis>=0.1.5
- anthropic>=0.69.0
- Git (for change detection and commits)
- Docusaurus (for the target documentation site)