
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


### Similar concepts

Can't someone just refer to a doc introduction or its meta description?

Introductions can be inconsistent across pages, varying in length from 1-2 sentences or several paragraphs.
The introductions can vary in detail, tone, or relation to the doc.
Introductions can range in purpose: "how to use," "what this covers," or technical background.
They can also become outdated as content evolves.

Meta descriptions are intended for use on search engine result pages.
They should be concise and contain target keywords to capture the relevant readers.
They're usually 130-140 characters, or 1-2 sentences long, which can be too short for complex topics.
Additionally, meta descriptions aren't present in the docs themselves (although one could create tooling to display them).

Generated summaries have the following advantages over intros and meta descriptions:
* Consistent in detail, length, tone, and format
* Adapts to different content types, such as tutorial or reference
* Long enough to provide a sufficient overview
* Current with the doc contents

## Prerequisites

* Python and packages:
   * Markdown analysis
   * Anthropic
* Docusaurus
* Github

### Docusaurus

The package is designed to run with the static site generator, Docusaurus, and
can also be used with other JavaScript-based sites.
The package can be adapted to work with other doc set configurations by changing how summaries are stored and imported.

### GitHub

`docdigest` assumes version control in a GitHub repository.
It detects files changed from a reference commit hash and only generates summaries for those files.
Version control is also important for the updated summaries.
Each updated summary is committed as a separate line change so that any change can easily be reverted back.

## Get started

Install `docdigest` as follows:

```sh
pip install markdown-analysis anthropic
cd <location of docdigest>
pip install .
```

Run the help command to verify that it's installed:

```sh
docdigest --help
```

## How to use docdigest

To use `docdigest`, all you need to do is:
1. Install the package in your Python environment
1. Create a configuration file
1. Call the program

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

# Run in automation mode
docdigest --automation --model claude
```

The following sections go into more detail about using `docdigest`.

## Configuration file

The default configuration file name is `docdigest_config.json`.

### Simple configuration

At the most basic level, list the source of your docs and where to write the output file.

```json
{
  "directory": "example-docs/docs/",
  "output_file": "example-docs/static/js/summaries.js"
}
```

### Advanced configuration

To further configure the summary generation, you can designate
file exclusions and the commit hash from when to evaluate content changes
(no summaries are generated if the content didn't change).

```json
{
  "directory": "example-docs/docs/",
  "commit": "a02e3da5f33ec2c605b110540c1ee844998a0856",
  "output_file": "example-docs/static/js/summaries.js",
  "exclude": {
    "files": ["tutorial-basics/create-a-document.md"],
  }
}
```

### Commit hash

For a first time run, you don't have a `commit` field so that all docs get processed.
Each subsequent iteration updates the commit hash to the latest version.
If no changes are detected, the `commit` field in the config file remains the same.


### File exclusions

To avoid summarizing certain files, list them in the `exclude` field.
You can specify exclusions by regex patterns, file names, and directory names.
Define exclusions relative to `directory`.

Additional exclude examples:

```json
  "exclude": {
    "directories": ["blog/", "archive/", "temp/"],
    "files": ["index.md", "404.md", "welcome.md"],
    "patterns": ["*/README.md", "**/CHANGELOG.md", "blog/**/*.md"]
  }
```

When files get removed from `exclude`, i.e., they're newly included,
then `docdigest` will summarize those files even if they're not changed.
In other words, when you have a commit specified in the configuration file,
`docdigest` summarizes both changed files and files that no longer get excluded.

## Execution modes

### Debug mode

Use debug mode to verify basic functionality of `docdigest`.
It does everything except call the LLM for summary generation.

Example output in `summaries.js`:

```
const intro = "Summary in debug mode. Headers: 5, Word count: 145, Random string: nqkpJ";
```

The output shows a count of headers, paragraph word count, and a random string.
The random string ensures that `summaries.js` is a changed file.
This reflects potential randomness in the LLM generating a different summary for the same content.

### LLM authentication

Claude requires an Anthropic API key in your environment variable.
For example:

```
export ANTHROPIC_API_KEY="your-key"
```

## How it works

The input to `docdigest` is a location to Markdown files and a commit hash provided in a JSON configuration file.
The output is a JavaScript file that contains the summary for each file.
Each summary is identified by an ID based on the Docusaurus ID if it exists, else the filename.

IDs are generated relative to the provided `directory` in the configuration.
For example, let's say the configuration references directory `docs`,
and `docs` has two subdirectories `tutorial` and `reference`.
The summary IDs will look like `tutorial_quickstart` or `reference_syntax`,
for `tutorial/quickstart.md` and `reference/syntax.md`, respectively.

At the first execution, the Markdown files are updated to import the summary using a variable.
With future iterations, only the summary file changes, not the Markdown files.

If there is an error generating a summary, the output file will exclude it,
and and the Markdown file will have the summary expander removed.

### Underlying stages

The tooling to generate AI summaries for the docs has the following stages, each corresponding to a Python module in this package.

1. 📖 Parse documentation
2. 🤖 Generate summaries (writes summaries.js)
   1. 🧮 Parallel option to dry-run (optional, exits early)
3. 📝 Update markdown imports (modifies .md files)
4. 📦 Commit changes (individual commits per summary)

For further details, see the [design docs](./design/).

### Package structure

```
docdigest
├── __init__.py
├── commitify.py
├── config.py
├── file_utils.py
├── git_utils.py
├── import_results.py
├── main.py
├── parse_docs.py
└── summarize.py
```

NOTE: If you update or add a module, also update `pyproject.toml` for GHA installation.

## Local development

Set up Python:

```
# create conda env
conda create --name summary
conda activate summary

# install packages
# uses conda when possible, pip otherwise
conda install anthropic
pip install markdown-analysis
```

Install application:

```
cd <docdigest root directory>
conda activate summary
pip install -e .
```

Download test docs:

```
# install fresh docusaurus
npx create-docusaurus@latest example-docs classic
```


## Troubleshooting

### Unclosed code fence

__Example error:__

```
🚨 Error parsing example-docs/docs/tutorial-basics/create-a-blog-post.md -- Unclosed code fence starting at line 36
```

__Meaning:__ For a code block denoted with the character sequence of three backticks (`\``) at the start and end, the parser couldn't detect the closing one from the line reported.

__Resolution:__ Confirm that each code block has the start and end character sequence. If the line reported is not a start sequence, evaluate the previous code block. Try adding a blank line before and after the character sequence.



