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

