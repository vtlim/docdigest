
### 2. LLM text generation

Testing stage: only use 2-3 docs for POC

 

Question Mark Open questions

Regarding tooling

What LLM family should we use? → Claude

What model should we use? → Sonnet, but also evaluate Haiku and Opus

Should we use a third-party API or the model provider directly? → direct

How to get a team token? → addressed

How much will this cost? → Possibly less than $6/month. See calculations here.
https://docs.google.com/spreadsheets/d/11qtod-K-dhctX6kHXWSIcQE-RTQPbAZB_gwIZswpZOU/edit?usp=sharingConnect your Google account 

 

Regarding input/processing

What prompt should we use?

prompt = f"Summarize {doc_text} using {extra_text} for context"

Besides paragraphs, what content should we give it for context? Strip or include:

Headers

Links

Images

Block quotes

Code blocks

Tables

Lists

What’s the average length of our docs?

What’s the LLM limit for token input?

What’s the theoretical limit of a Python string variable? → most likely limited by RAM so not something we’d have to worry about for an individual doc

Do we want to augment the provided information with other sources with retrieval-augmented generation (RAG)? 
RAG can improve accuracy, enhance relevance, reduce hallucinations.

Any of the non-paragraph text

Splunk docs

Content from another doc (intro? section? whole doc?)

If we apply RAG to supply context from other internal docs,

Cut off by similarity score?

Cut off by top N matches?

 

Regarding output

How long should the summaries be?

 


Comparison of tools










 

### 3. Summary imports
Plan
 Store all summaries as individual variables in a .js file. Import the appropriate variable in the Markdown docs file.

Modeled after version.js and how it’s used



import {DRUIDVERSION, IMPLYVERSION, imply_agent} from "@site/static/js/versions.js"
 

Summary placement

Top of each doc as an expander that’s default open

Landing page for a section (e.g., send events)

Google preview description

New content announcements (changelog)


### 4. Commit changes

From an existing summaries.js, compare a new summaries.js file. For each new or changed line, update the existing summaries.js file and commit this change in the PR.

Main execution
Import modules of the package for end-to-end execution

python main.py --config docs.json



from . import parse_docs
from . import import_summaries
from .summarize import claude
changed_files = parse_docs.get_files(DIR_NAME, COMMIT_HASH)
doc_contents = parse_docs.read_changes(changed_files)
...
Automation
For the automation:

Use GitHub Actions to generate/refresh doc summaries.

Create a pull request of the changes for a writer to review.

Run at what cadence Question Mark

Separate each change as an individual commit. That way if we want to revert a change, we can just revert the commit(s).

