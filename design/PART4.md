## 4. Commit changes

### Goal

Detect changes in `summaries.js` from a previously existing version.
Separate each change as an individual commit. That way if we want to revert a change, we can just revert the commit.

### Requirements

* Run a diff operation to detect individual line changes in `summaries.js` from a previously existing file.
* For each new or changed line, create a separate `git add` and `git commit`.
* Describe each commit message based on the change: `[Added/removed/updated] summary for [variable]`
   * An "update" commit only changes `summaries.js`
   * An "add or remove" commit changes `summaries.js` and the corresponding Markdown file
* Add a mode or flag to determine whether the program is called by a user or running in an automated workflow.
If it's called by a user, prompt the user to check whether they're on the right branch and if they want to create a new one before doing the series of git commits.
