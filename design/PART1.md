## 1. Markdown parsing

### Goal

Parse the Markdown docs and store each file’s content as a string.

### Tools

* [markdown-analysis](https://pypi.org/project/markdown-analysis/)

This module can parse elements of a Markdown file, such as headers, lists, and images.

Example usage:

```python
from mrkdwn_analysis import MarkdownAnalyzer
analyzer = MarkdownAnalyzer("path/to/document.md")
paragraphs = analyzer.identify_paragraphs()

# convert `paragraphs` into a string variable
# that contains all of the document's contents
...
```

### Requirements

* Develop the above, and extend it to analyze all Markdown files. Ignore non-MD files such as tags.yml and assets.

* Consider what’s best for a return type. One option could be a dictionary:
   ```
   {
     "ref_s2s": "all the words in the s2s doc. this will be a really long string",
     "send_events_splunk_hec": "all the words in the hec doc. also long string",
     ...
   }
   ```

* Convert hyphens in filenames to underscores to adhere to valid Python variable naming.

* Read from a commit hash and only parse files that have been changed since that. Store the current commit hash for future runs.

* Read a directory location (don’t hard-code to any folder).

* Use a JSON configuration file to read both the directory location and the commit hash. That way we have version control over the variables and create other configuration files for other use cases.
For example, 

   ```
   {
     "directory": "lumi/",
     "commit": "e4526da1d45a107780a932ccc46697fcd15f9bcb"
   }
   ```

* Develop a separate function for these:
  * `get_files()`: Get list of changed docs from a specified directory based on the commit difference
  * `parse_doc()`: Parse content from an individual doc

### Results

Parsed headers are all correct.

For the parsed paragraphs:

**Not included**
- Lists: Ordered or unordered lists, such as prerequisites or numbered steps in tutorials.
   - [ ⚠️ inconsistent ] Content within a list is included if it follows a line break.
   - [ ⚠️ inconsistent ] The paragraph after a list can be missed.
   - ✅ HTML list items, such as the processor examples that use a definition list `<dl>`, are excluded.
   - [ ⚠️ lacking ] Reference pages that predominatly use bullet points (permissions) only rely on the introduction.
   - ✅ Reference pages that use un-bulleted text (glossary) contain the full reference content.
- [ ⚠️ extraneous ] Assets: References to images, although occasionally one slips through.
- ✅ Code blocks.
- ✅ Tables.

**Included**
- [ ❌ extraneous ] Links: Hyperlinks within the text.
- [ ⚠️ extra syntax but ok ] Admonitions: Content of admonitions as well as `:::` syntax (start and close).
- ✅ Expanders: Content and assets in expanders, excluding the expander title.

**Resulting modifications**
- Remove links, including asset references checking for `[]()`

Consider including list items when the paragraph word count is below a certain threshold.
