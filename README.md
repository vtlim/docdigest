
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

If you're only running the summary generation a single time, you don't have to use a GitHub repository.

It's required when you specify a reference commit hash in the `docdigest` configuration.
The application uses git to detect which files have changed since that commit and only generates summaries for those files.
When you commit changes made by `docdigest`, the changes for each doc are committed separately so that you can `git revert` any doc you don't want to update.


## Get started

### Install

To install `docdigest`:

```sh
pip install markdown-analysis anthropic
cd <location of docdigest>
pip install .
```

Run the help command to verify that it's installed:

```sh
docdigest --help
```

### Quickstart

To use `docdigest`:

1. Assign your Anthropic API key to the environment variable `ANTHROPIC_API_KEY`. For example:
   ```sh
   export ANTHROPIC_API_KEY="your-key"
   ```

1. Create a configuration file `docdigest_config.json`. Update the configuration to point to your input docs and designate where to write the output file.

   <details><summary>Basic template</summary>

   ```
   {
     "directory": "example-docs/docs/",
     "output_file": "example-docs/static/js/summaries.js",
     "summary_template": "docdigest_template.md"
   }   
   ```
   </details>

1. Create a template file, `docdigest_template.md`. Replace the example link in the footer text.
Optionally, you can change the summary expander title, change the footer text, or remove the footer altogether.

   <details><summary>Basic configuration</summary>

   ```
   import {{variable_name}} from "{import_path}"
   
   <details>
   <summary>AI summary</summary>
   
   {{variable_name}}
   
   <br/><br/>
   <span className="small-font">
   <i>
   <a href="https://example.com/">About AI summaries.</a>
   </i>
   </span>
   
   </details>
      
   ```
   </details>

1. Perform a dry run. This allows you to verify the file processing without calling the API yet.

   ```
   docdigest  --llm none
   ```

1. When asked whether to commit, type `n`.
1. Review the output in your terminal. Ensure that it lists the correct set of docs and that the output is where you intend.
1. View the summary components. Preview the docs such as using `npm run start`. If you're in a git repository, you can view line changes with `git diff`.
1. If everything looks as expected, generate the summaries themselves:

   ```
   docdigest
   ```

The following sections go into more detail about using `docdigest`.
For a reference list of commands, see [Commands](./COMMANDS.md).

## Configuration file

`docdigest` takes a JSON configuration file that describes the
location of the source files, the output file, any
file exclusions, and an optional reference commit hash.

### Default file name

The default configuration file name is `docdigest_config.json`.
To specify a custom configuration in your request:

```
docdigest --config docdigest_custom.json
```

### Required properties

```json
{
  "directory": "example-docs/docs/",
  "output_file": "example-docs/static/js/summaries.js",
  "summary_template": "docdigest_template.md"
}
```

The basic configuration requires the following properties:

* `directory`: the source folder of your docs, relative to where you call `docdigest`
* `output_file`: where to write the output file, relative to where you call `docdigest`
* `summary_template`: file containing the template of the summary component to import

In the summary template, you can customize the imported HTML component, such as
its title and any preamble or closing text.
Be sure to retain anything with curly braces `{}`, and keep the newline at the end of the template.

### Additional configuration

```json
{
  "directory": "example-docs/docs/",
  "output_file": "example-docs/static/js/summaries.js",
  "summary_template": "docdigest_template.md",
  "exclude": {
    "files": ["tutorial-basics/create-a-document.md"],
  },
  "commit": "a02e3da5f33ec2c605b110540c1ee844998a0856"
}
```

To further configure the summary generation, you can designate
file exclusions and the commit hash from when to evaluate content changes
(no summaries are generated if the content didn't change).

#### File exclusions

```json
  "exclude": {
    "directories": ["blog/", "archive/", "temp/"],
    "files": ["index.md", "404.md", "welcome.md"],
    "patterns": ["*/README.md", "**/CHANGELOG.md", "blog/**/*.md"]
  }
```

To avoid summarizing certain files, list them in the `exclude` field.
You can specify exclusions by directory names, file names, and regex patterns.

Important things to note:

* The `exclude` patterns are relative to the `directory` parameter (whereas `directory` and `output_file` are relative to where you call `docdigest`).
* For directories and files, regex is NOT supported.
* When you remove something from `exclude`, then it'll get summarized whether or not the file changed.

#### Commit hash

Summaries are only generated from files changed from the provided commit hash.

For a first time run, don't include the `commit` field so that all docs get processed.
Each subsequent iteration automatically updates the commit hash to the latest version.
If no changes are detected, the `commit` field in the config file remains the same.

If you add a new file that has NOT been committed, then git doesn't detect it
as a changed file relative to the listed commit hash. That means it won't get summarized.
You need to commit the new file before `docdigest` can summarize it.

## LLMs

Use the `--llm` flag to specify which model to use, currently `none` or `claude`.
The default is `none` which performs a dry run and doesn't make any API calls.
This package can be extended to include other models like GPT.

### Dry run

Perform a dry run to verify basic functionality of `docdigest`.
It does everything except call the LLM for summary generation.
To do a dry run:

```
docdigest --llm none
```

Example output in `summaries.js`:

```
const intro = "Summary in dry run mode. Headers: 5, Word count: 145, Random string: nqkpJ";
```

The output shows a count of headers, paragraph word count, and a random string.
The random string ensures that `summaries.js` is a changed file.
This reflects potential randomness in the LLM generating a different summary for the same content.

### Claude

First estimate costs to make sure you're parsing the right content and generating the correct IDs:

```
docdigest --llm claude --estimate-cost
```

If everything looks correct, run the summarization:

```
docdigest --llm claude
```

You can also run `docdigest` without any user prompts.
This is intended for use in a continuous integration platform like GitHub Actions.
To summarize in an automated CI setup:

```
docdigest --automation --llm claude
```

The automation mode automatically creates a new branch called `bot-summaries`.
If the branch already exists, it overwrite the contents of the branch.
The program then commits each change separately and creates a PR against the main branch.
Commits are kept separate so that it's easier to revert if desired.


## Meta descriptions

You can also generate meta descriptions separately from summarization.
This also uses Claude, with an available `--estimate-cost` option.

When run locally, the program checks for `description` in the front matter
of the Markdown files. It updates the description field if present and adds it if not.
You can then create a branch, add those files, then commit and push the changes.
To generate meta descriptions locally:

```
docdigest --generate meta-descriptions
```

The automation mode is designed to run in a PR that contains changed Markdown files.
The program parses the docs, uses Claude to generate summaries for only the changed files,
then creates a comment in the PR that has a list of meta description suggestions.
You can then manually edit the files to include the descriptions.
To generate meta descriptions in an automated workflow:

```
docdigest --generate meta-descriptions --automation
```

Note that the automation mode can't create inline suggestions for the
changed files since the front matter content may not be in the PR diff context.
In other words, you can't make a suggestion at line 3 when the only change
in the doc is at line 50.

## Remove a summary

To remove a summary, revert the git commit that introduced the summary.
This removes the following content:

* `summaries.js` file:
   * `const` summary variable
   * corresponding line in `module.exports`
* Markdown file:
   * import summary line
   * `<details>` block with the summary

Optionally, update the `docdigest` configuration to list that file in the exclusions.

To reset the docs and remove all summaries, update the exclude pattern.
You can't exclude everything (`"exclude": {"**"}`), since it's like telling the program to run on no files.
The easiest way is to exclude everything except 1+ existing file.

Note that you can't create a dummy file for this process unless you commit it first, set the exclusions, run the program, then remove the dummy file. But then it's kind of like doing the previous method anyway.

## Content requirements

`docdigest` has been successfully tested on a doc set of 75 topics containing over 53k tokens.
The doc set contained elements including tables, lists, images, code blocks, and HTML elements such as expanders.

To successfully run this program, ensure that each of your Markdown files:
* Uses valid Markdown syntax
* Contains YAML frontmatter at the top of the page
* Is tracked by git (if you use the `commit` parameter)

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

__Error handling__: If there is an error generating a summary, it won't be included in the output file nor the Markdown file.
If there was a summary component in the Markdown file, it gets removed.

For more technical details, see the [design docs](./design/index.md) and the diagram within.

## Troubleshooting

### Unclosed code fence

__Example error:__

```
🚨 Error parsing example-docs/docs/tutorial-basics/create-a-blog-post.md -- Unclosed code fence starting at line 36
```

__Meaning:__ For a code block denoted with the character sequence of three backticks (`\``) at the start and end, the parser couldn't detect the closing one from the line reported.

__Resolution:__ Confirm that each code block has the start and end character sequence. If the line reported is not a start sequence, evaluate the previous code block. Try adding a blank line before and after the character sequence.

### Failed to get changed files

__Example error:__

```
Error: 🚨 Failed to get changed files since commit 74001ed173fab75acbcf939ede865df0f02b6bbc
```

__Meaning:__ Git can't recognize the commit hash provided in the `docdigest` configuration.

__Resolution:__ Ensure that the commit hash is a valid hash from the main branch. It can't be a hash from a branch, such as copied from a pull request. Check for any typos or trailing spaces.
