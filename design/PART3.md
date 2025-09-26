## 3. Summary imports

### Goal

With each summary as an individual variable in a .js file, import the corresponding variable in the Markdown doc.

### Requirements

* For each output summary, ensure that the corresponding file imports the content from the `summaries.js` file.
* Following the import, create an expander object that calls the variable to display.
* Ensure that the import and expander are only present a single time at the top of the doc and after the docs front matter (enclosed by three dashes).
* Ensure that if a file doesn't have a summary, it doesn't have an import or expander. Remove it if it's already there.

| Current State | Should Have | Action |
|---------------|-------------|---------|
| Has component | Has summary | ✅ No changes |
| Has component | No summary | 🗑️ Remove component |
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

