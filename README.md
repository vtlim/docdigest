
## `docdigest`

The Python package `docdigest` creates AI summaries for Markdown-based documentation.
The summarization is AI-powered and user-controlled.
It's intended for automation with CI tools but can also be run manually.

The package is designed to run with the static site generator, Docusaurus, and
can also be used with other JavaScript-based sites.
The package can be adapted to work with other doc set configurations by changing how summaries are stored and imported.

`docdigest` assumes version control in a GitHub repository.
It detects files changed from a reference commit hash and only generates summaries for those files.
The version control is also important for the updated summaries.
Each updated summary is committed as a separate line change so that any change can easily be reverted back.

The input is a collection of Markdown files and a commit hash,
and the output is a single file that contains a summary for each file, with one summary per line.
The Markdown files themselves will only have a one-time change to import the summary using a variable.
With all future iterations, only the summary file changes.

From the perspective of a docs reader, the top of each page will show an expander
that summarizes the article. The content of the expander comes from the summary file.

## Prerequisites

* Python
* Docusaurus
* Github

## Description of components

The tooling to generate AI summaries for the docs has the following components.

1. [Markdown parsing](./PART1.md)
1. LLM text generation
1. Summary imports
1. Commit changes

## How to use

### Input configuration file

```
{
  "directory": "example-docs/docs/tutorial-basics/",
  "commit": "a02e3da5f33ec2c605b110540c1ee844998a0856"
}
```

For a first time run, omit `commit` from the configuration to process all docs.

Subsequent iterations of calling `docdigest` updates the commit hash to the latest version.
If no changes are detected, the config file remains the same.

### Commands to run

```
# Use default config
docdigest

# Specify custom config
docdigest --config my_config.json

# Custom output file
docdigest --config docdigest_config.json --output static/js/summaries.js
```

## Package structure

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

## Local development

Set up your local machine:

```
# create conda env
conda create --name summary
conda activate summary

# install packages
conda install anthropic

# install fresh docusaurus
npx create-docusaurus@latest example-docs classic
```

For iterative development:

```
conda activate summary
pip install -e .
```

## Troubleshooting

### Unclosed code fence

__Example error:__

```
🚨 Error parsing example-docs/docs/tutorial-basics/create-a-blog-post.md -- Unclosed code fence starting at line 36
```

__Meaning:__ For a code block denoted with the character sequence of three backticks (`\``) at the start and end, the parser couldn't detect the closing one from the line reported.

__Resolution:__ Confirm that each code block has the start and end character sequence. If the line reported is not a start sequence, evaluate the previous code block. Try adding a blank line before and after the character sequence.



