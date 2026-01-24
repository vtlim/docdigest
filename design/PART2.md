## 2. LLM text generation

### Goal
In `summarize.py`, generate short text summaries for each file parsed in the previous stage.

### Tools

* [Anthropic Python API library](https://github.com/anthropics/anthropic-sdk-python)

### Requirements

Technical requirements that don't include the variable components of summarization.

#### Input and output

* Read in the dictionary of file IDs and contents from `parse_docs.py`
* Create a summary for each entry in the dictionary
* Write the output content which has a structure similar to the following:

   ```js
   /*
   Summaries for each topic, matched by filename
   */
   
   const congratulations = "summary for congratulations";
   const create_a_blog_post = "summary for create_a_blog_post";
   
   
   module.exports = {
     congratulations,
     create_a_blog_post
   };
   ```

* Store the output in a file designated by `output_file` in the config file that was also used by `parse_docs.py`

#### Structure

Use the following functions to structure this package:
* A main function that reads the dictionary, provide content to summarize, and stores results to write
* `summarize(prompt, content, model, context)` to generate the summary 
     * `prompt` is a string variable that contains the LLM prompt
     * `model` is a variable that can take the value `dummy` or `claude`
        * `dummy` means to return the text `"dummy"` for each summary
        * `claude` means to generate each summary using Claude from the Anthropic module
        * `context` is an optional string variable that can provide more information for the summarization
* `format_results()` that formats the results for a JavaScript file using the structure above
* `store_results(output_file)` that writes the results to the specified location `output_file`

For initial development, only consider the content above.
Do not explore the prompt, evaluation, or additional considerations below.

### Summmarization

Various modes of summarization (basic or advanced) and to debug the package independent of summarization.

#### Debug mode

Generates dry run text without any API calls.

The debug value lists the header count and word count of the input text.

Example:

```
const intro = "Summary in debug mode. Headers: 5, Word count: 145";
```

#### Basic mode

Generates a basic summary using input paragraphs with possible consideration of headers.

#### Advanced mode

RAG-like workflow with semantic search.

Workflow
1. __Semantic indexing__: Generate initial summaries for all docs
2. __Semantic search__: Find related docs measured by TF-IDF with cosine similarity
3. __Enhanced context__: Builds context using the related docs
4. __Summarize__: Summarize the main doc with context on the related docs

Semantic search focuses on meaning and context of the query.
In this context, a semantic approach evaluates the relationship of the present text to summarize with other docs.
The goal is more accurate and more relevant results.

### Prompt

Ideas for prompts for basic summarization with simple context.

#### Basic content only

```
You are a technical documentation summarizer. Your task is to create concise, informative summaries for documentation pages.
The summary will be displayed in an expandable section at the top of the documentation pages.

**Instructions:**
- For the provided content, summarize the main purpose and key information
- Focus on what the reader will learn or accomplish
- Write it for an audience of developers or technical users
- Use plain text between 25-40 words and no special formatting
- Use clear, accessible language that matches the original tone
- Avoid unnecessary jargon unless it's essential to understanding
- Make the summary standalone - someone should understand the page's value without reading the full content

**Content to summarize:**
[DOCUMENT_CONTENT_HERE]

Provide only the summary text, nothing else.
```

#### Modification with headers

```
SUMMARIZATION_PROMPT = """Create a concise 1-2 sentence summary.

Document headers (main topics): {headers}
Document content: {content}

Focus on the main topics indicated by the headers while summarizing the content.

Summary:"""
```

### Evaluation 

Does it improve accuracy or relevance when we provide more content in the context?

* Headers
* Block quotes
* Code blocks
* Tables
* Lists

Exclude the following content as inputs:
* Links
* Images

### Additional considerations

#### RAG

Consider augmenting the provided information with other sources using retrieval-augmented generation.
RAG can improve accuracy, enhance relevance, reduce hallucinations.

* Any of the non-paragraph text
* Splunk docs
* Content from other docs in the same set (intro? section? whole doc?)

If we apply RAG to supply context from other internal docs,
* Cut off by similarity score?
* Cut off by top N matches?

#### Prompt caching

Consider prompt caching for the entire doc set to reduce time and costs of supplying it for context at each run.
It's unclear whether prompt caching would have any benefit for this use case since the cache time is 5 minutes
by default and can be configured up to one hour. However, the write tokens are more expensive than the base price.
