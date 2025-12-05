
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

`docdigest` was developed using the following tools:

* Python and packages:
   * Markdown analysis
   * Anthropic (for Claude)
* Docusaurus
* GitHub

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

Install `docdigest`:

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

1. Install the package in your Python environment. See [Get started](#get-started).

1. Ensure you have an Anthropic API key as the environment variable `ANTHROPIC_API_KEY`. For example:
   ```sh
   export ANTHROPIC_API_KEY="your-key"
   ```

1. Create a configuration file.  
   Default name: `docdigest_config.json`

1. Call the program.  
   Quickstart command: `docdigest`

The following sections go into more detail about using `docdigest`.
For a reference list of commands, see [Commands](./COMMANDS.md).

## Configuration file

The default configuration file name is `docdigest_config.json`.
To specify a custom configuration:

```
docdigest --config docdigest_custom.json
```

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

Summaries are only generated from files changed from the provided commit hash.

For a first time run, don't include the `commit` field so that all docs get processed.
Each subsequent iteration automatically updates the commit hash to the latest version.

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

## Execution models

You can use either the `debug` or `claude` model.
The program runs in `debug` mode by default.
You can also extend this package to include other LLM models like GPT.

### Debug

Use debug mode to verify basic functionality of `docdigest`.
It does everything except call the LLM for summary generation.
To use debug mode:

```
docdigest --model debug
```

Example output in `summaries.js`:

```
const intro = "Summary in debug mode. Headers: 5, Word count: 145, Random string: nqkpJ";
```

The output shows a count of headers, paragraph word count, and a random string.
The random string ensures that `summaries.js` is a changed file.
This reflects potential randomness in the LLM generating a different summary for the same content.

### Summarize with Claude

First estimate costs to make sure you're parsing the right content and generating the correct IDs:

```
docdigest --model claude --dry-run
```

If everything looks correct, run the summarization:

```
docdigest --model claude
```

Summarization is also available in automation mode, intended for use in
a continuous integration platform like GitHub Actions.
To summarize in automation mode:

```
docdigest --automation --model claude
```

The automation mode automatically creates a new branch called `bot-summaries`.
If the branch already exists, it overwrite the contents of the branch.
The program then commits each change separately and creates a PR against the main branch.
Commits are kept separate so that it's easier to revert if desired.


## Meta descriptions

You can also generate meta descriptions separately from summarization.
This also uses Claude, with an available `--dry-run` option.

When run locally, the program checks for `description` in the front matter
of the Markdown files. It updates the description field if present and adds it if not.
You can then create a branch, add those files, then commit and push the changes.
To generate meta descriptions locally:

```
docdigest --meta
```

The automation mode is designed to run in a PR that contains changed Markdown files.
The program parses the docs, uses Claude to generate summaries for only the changed files,
then creates a comment in the PR that has a list of meta description suggestions.
You can then manually edit the files to include the descriptions.
To generate meta descriptions in an automated workflow:

```
docdigest --meta --automation
```

Note that the automation mode can't create inline suggestions for the
changed files since the front matter content may not be in the PR diff context.
In other words, you can't make a suggestion at line 3 when the only change
in the doc is at line 50.

## How it works

__Input and output__: The input to `docdigest` is a location to Markdown files and a commit hash provided in a JSON configuration file.
The output is a JavaScript file that contains the summary for each file.

__Summary ID__: Each summary is identified by an ID based on the Docusaurus ID if it exists, else the filename.
IDs are generated relative to the provided `directory` in the configuration.

For example, let's say the configuration references directory `docs`,
and `docs` has two subdirectories `tutorial` and `reference`.
The summary IDs will look like `tutorial_quickstart` or `reference_syntax`,
for `tutorial/quickstart.md` and `reference/syntax.md`, respectively.

__Changed files__: At the first execution, the Markdown files are updated to import the summary using a variable.
With future iterations, only the summary file changes, not the Markdown files.

__Error handling__: If there is an error generating a summary, the output file will exclude it,
and and the Markdown file will have the summary expander removed.

For more technical details, see the [design docs](./design/).

## Remove a summary

To remove a summary, you just need to revert the git commit that introduced the summary.
This removes the following content:

* `summaries.js` file:
   * `const` summary variable
   * corresponding line in `module.exports`
* Markdown file:
   * import summary line
   * `<details>` block with the summary

Optionally, update the `docdigest` configuration to list that file in the exclusions.

## Troubleshooting

### Unclosed code fence

__Example error:__

```
🚨 Error parsing example-docs/docs/tutorial-basics/create-a-blog-post.md -- Unclosed code fence starting at line 36
```

__Meaning:__ For a code block denoted with the character sequence of three backticks (`\``) at the start and end, the parser couldn't detect the closing one from the line reported.

__Resolution:__ Confirm that each code block has the start and end character sequence. If the line reported is not a start sequence, evaluate the previous code block. Try adding a blank line before and after the character sequence.



