---
sidebar_position: 5
---



import {tutorial_basics_deploy_your_site} from "@site/static/js/summaries.js"

<details>
<summary>AI summary</summary>

{tutorial_basics_deploy_your_site}

<br/><br/>
<span className="small-font">
<i>
<a href="https://docs.imply.io/lumi/">About AI summaries.</a>
</i>
</span>

</details>

# Deploy your site

Docusaurus is a **static-site-generator** (also called **[Jamstack](https://jamstack.org/)**).

It builds your site as simple **static HTML, JavaScript and CSS files**.

## Build your site

Build your site **for production**:

```bash
npm run build
```

The static files are generated in the `build` folder.

## Deploy your site

Test your production build locally:

```bash
npm run serve
```

The `build` folder is now served at [http://localhost:3000/](http://localhost:3000/).

You can now deploy the `build` folder **almost anywhere** easily, **for free** or very small cost (read the **[Deployment Guide](https://docusaurus.io/docs/deployment)**).