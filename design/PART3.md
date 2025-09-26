## 3. Summary imports

### Goal

With each summary as an individual variable in a .js file, import the corresponding variable in the Markdown doc.

### Assumptions

The JavaScript file must be located in the `static/js` folder of the Docusaurus site (wherever you call `npm run start` or `docusaurus start` or `yarn start`).
That may be the root of the Docusaurus directory or in the `website` subdirectory.

### Requirements

* For each output summary, ensure that the corresponding file imports the content from the `summaries.js` file.
* Following the import, create an expander object that calls the variable to display.
* Ensure that the import and expander are only present a single time at the top of the doc and after the docs front matter (enclosed by three dashes).
* Ensure that if a file doesn't have a summary, it doesn't have an import or expander. Remove it if it's already there.

| Current State | Should Have | Action |
|---------------|-------------|---------|
| Has component with **same variable** | Has summary | ✅ No changes |
| Has component with **different variable** | Has summary | 🔄 Remove old, add new |
| Has component with **any variable** | No summary | ⛔ Remove component |
| No component | Has summary | ➕ Add component |
| No component | No summary | ✅ No changes |

### Example import

```
---
id: congratulations
title: Congratulations
---

import {congratulations} from "@site/static/js/summaries.js"


<details open>
<summary>Summary</summary>

{congratulations}

<br/><br/>
<span className="small-font">
This summary was generated using AI.
Check important info for mistakes.
</span>

</details>
```

### How to undo all imports

Use the `exclude` field in the `docdigest` configuration to exclude all files except one.
(If it detects no files changed or excluded, the program stops all processing.)

When you exclude the files, the `imports.py` stage removes summaries since those files are noted for exclusion.

Then run the program again and update `exclude` to exclude that last file, or else just remove the component manually.
