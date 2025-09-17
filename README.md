
## `docdigest`

This project is a new Python package called `docdigest`.
The goal is to create AI summaries for each Markdown page in a technical documentation repository.
The summarization will be AI-powered but user-controlled.

The input is a collection of Markdown files,
and the output is a single file that contains a summary for each file, with one summary per line.

From the perspective of a docs reader, the top of each page will show an expander
that summarizes the article. The expander content comes from the summary file.

## Description of components

The tooling to generate AI summaries for the docs has the following components.

1. [Markdown parsing](./PART1.md)
1. LLM text generation
1. Summary imports
1. Commit changes

### Proposed structure

```
docdigest
├── __init__.py
├── commitify.py                   # part 4
├── main.py                        # puts together parts 1-3
├── import_summaries.py            # part 3
├── parse_docs.py                  # part 1
└── summarize                      # part 2
    ├── claude.py
    └── gpt.py
```

### Local development setup

```
# create env
conda create --name summary
conda activate summary

# install packages
conda install anthropic

# install fresh docusaurus
npx create-docusaurus@latest example-docs classic
```
