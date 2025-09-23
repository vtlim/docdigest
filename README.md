
## `docdigest`

The Python package `docdigest` creates AI summaries for Markdown-based documentation.
The summarization is AI-powered and user-controlled.
It's intended for automation with CI tools but can also be run manually.

From the perspective of a docs reader, the top of each page will show an expander
that summarizes the article.

## Why

Oftentimes, the way to get acquainted with a new doc is to do some combination of the following:
* Scan the title
* View the internal table of contents
* Read the introduction
* See where the doc is in context of other docs

What if there was a better way to help readers get to the point?
That's where top-level summaries come in.
These are short blurbs for users to quickly scan before diving into the content.
A summary can help users confirm they're in the right place.
By knowing what lies ahead, it can also help reduce cognitive load ("tell them what you're going to tell them").

Why not refer to a doc introduction or its meta description?

Introductions can be inconsistent across pages, varying in length from 1-2 sentences or several paragraphs.
The introductions can vary in detail, tone, or relation to the doc.
Introductions can range in purpose: "how to use," "what this covers," or technical background.
They can also become outdated as content evolves.

Meta descriptions are intended for use on search engine result pages.
They should be concise and contain target keywords to capture the relevant readers.
They're usually 130-140 characters, or 1-2 sentences long, which can be too short for complex topics.
Additionally, meta descriptions aren't present in the docs themselves,
although one could create tooling to display them.

Generated summaries have the following advantages over intros and meta descriptions:
* Consistent in detail, length, tone, and format
* Adapts to different content types, such as tutorial or reference
* Long enough to provide a deeper overview than meta descriptions
* Current with the doc contents
* Standard placement across all topics


## Prerequisites

* Python
* Docusaurus
* Github

### Docusaurus

The package is designed to run with the static site generator, Docusaurus, and
can also be used with other JavaScript-based sites.
The package can be adapted to work with other doc set configurations by changing how summaries are stored and imported.

### GitHub

`docdigest` assumes version control in a GitHub repository.
It detects files changed from a reference commit hash and only generates summaries for those files.
The version control is also important for the updated summaries.
Each updated summary is committed as a separate line change so that any change can easily be reverted back.

## How to use

### Input configuration file

```
{
  "directory": "example-docs/docs/tutorial-basics/",
  "commit": "a02e3da5f33ec2c605b110540c1ee844998a0856",
  "output_file": "example-docs/static/js/summaries.js"
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
docdigest --config docdigest_config.json

# Specify summarization model
docdigest --model [claude,debug]
```

## Operational details

The input to `docdigest` is a location to Markdown files and a commit hash provided in a JSON configuration file.
The output is a JavaScript file that contains the summary for each file.

The Markdown files themselves will have a one-time change to import the summary using a variable.
With all future iterations, when the summarizations are successful, only the summary file changes.
If there is an error generating a summary, the output file will exclude it,
and and the Markdown file will have the summary expander removed.

## Description of components

The tooling to generate AI summaries for the docs has the following components.

1. [Markdown parsing](./design/PART1.md)
1. LLM text generation
1. Summary imports
1. Commit changes

## Package structure

```
docdigest
├── __init__.py
├── commitify.py
├── config.py
├── import_js.py
├── main.py
├── parse_docs.py
└── summarize.py
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



