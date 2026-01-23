/*
Summaries for each topic, matched by filename
*/

const intro = "Learn how to quickly set up a new Docusaurus site using the classic template. Install dependencies and run a local development server. Edit documentation files and see changes reload automatically in your browser.";
const tutorial_basics_congratulations = "This page concludes the Docusaurus basics tutorial and suggests next steps like exploring versioning and internationalization features. It encourages reporting any tutorial issues on GitHub.";
const tutorial_basics_create_a_document = "Documents are grouped pages organized in a docs folder. Docusaurus automatically generates sidebars from your Markdown files. You can customize sidebar labels and positioning using metadata.";
const tutorial_basics_create_a_page = "Create standalone pages by adding Markdown or React files to the src/pages directory. Files automatically become accessible routes. Simple setup requires no additional configuration.";
const tutorial_basics_deploy_your_site = "Docusaurus generates static HTML, CSS, and JavaScript files for production deployment. Build outputs go to a folder you can test locally. Deploy these static files anywhere easily and affordably.";
const tutorial_extras_manage_docs_versions = "Docusaurus supports multiple documentation versions by copying the docs folder into versioned directories and tracking them in versions.json. Add a navbar dropdown to let users switch between versions easily.";
const tutorial_extras_translate_your_site = "This guide explains how to set up multilingual support in Docusaurus by translating documentation files. It covers configuring locales, translating content, testing translations locally, and building sites for multiple languages.";


module.exports = {
  intro,
  tutorial_basics_congratulations,
  tutorial_basics_create_a_document,
  tutorial_basics_create_a_page,
  tutorial_basics_deploy_your_site,
  tutorial_extras_manage_docs_versions,
  tutorial_extras_translate_your_site
};
