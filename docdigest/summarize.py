"""
AI summarization functionality for docdigest.
Generates short text summaries for documentation content and formats them as JavaScript modules.
"""

from typing import Dict, List, Optional

# Global prompt for summarization
SUMMARIZATION_PROMPT = """Create a concise 1-2 sentence summary.

Document headers (main topics): {headers}
Document content: {content}

Focus on the main topics indicated by the headers while summarizing the content.

Summary:"""

# JavaScript module header comment
JS_MODULE_HEADER = """/*
Summaries for each topic, matched by filename
*/

"""


def summarize_debug(parsed_doc: Dict[str, List[str]]) -> str:
    """
    Debug summarization that returns a placeholder string with structure info.

    Args:
        parsed_doc: Dictionary with "headers" and "paragraphs" lists

    Returns:
        Debug placeholder string with header and word counts
    """
    header_count = len(parsed_doc.get("headers", []))
    word_count = sum(len(p.split()) for p in parsed_doc.get("paragraphs", []))
    return f"Summary in debug mode. Headers: {header_count}, Word count: {word_count}"


def summarize_claude(parsed_doc: Dict[str, List[str]]) -> str:
    """
    Claude summarization with header-aware prompting.

    Args:
        parsed_doc: Dictionary with "headers" and "paragraphs" lists

    Returns:
        Generated summary string
    """
    headers_text = ", ".join(parsed_doc.get("headers", []))
    content_text = " ".join(parsed_doc.get("paragraphs", []))

    # Use the global prompt template with header emphasis
    # For now, return placeholder since Claude API integration not implemented
    return "TODO"


def summarize(model: str, parsed_doc: Dict[str, List[str]] = None) -> str:
    """
    Generate summary using specified model.

    Args:
        model: Model to use ("debug" or "claude")
        parsed_doc: Dictionary with "headers" and "paragraphs" lists (needed for both models)

    Returns:
        Generated summary string

    Raises:
        ValueError: If unknown model specified
    """
    if model == "debug":
        return summarize_debug(parsed_doc)
    elif model == "claude":
        return summarize_claude(parsed_doc)
    else:
        raise ValueError(f"Unknown model: {model}")


def format_results(summaries: Dict[str, str]) -> str:
    """
    Format summary results as JavaScript module.

    Args:
        summaries: Dictionary mapping variable names to summary strings

    Returns:
        JavaScript module string with const declarations and exports
    """
    if not summaries:
        return JS_MODULE_HEADER + "module.exports = {};\n"

    # Generate const declarations
    const_declarations = []
    export_names = []

    for var_name, summary in summaries.items():
        # Escape quotes in summary
        escaped_summary = summary.replace('"', '\\"')
        const_declarations.append(f'const {var_name} = "{escaped_summary}";')
        export_names.append(var_name)

    # Build the complete JavaScript module
    js_content = JS_MODULE_HEADER
    js_content += '\n'.join(const_declarations)
    js_content += '\n\n\nmodule.exports = {\n'
    js_content += ',\n'.join(f'  {name}' for name in export_names)
    js_content += '\n};\n'

    return js_content


def store_results(content: str, output_file: str) -> None:
    """
    Write formatted results to specified file.

    Args:
        content: JavaScript module content to write
        output_file: Path to output file
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Summaries written to: {output_file}")
    except Exception as e:
        raise RuntimeError(f"Failed to write to {output_file}: {e}")


def generate_summaries(parsed_docs: Dict[str, Dict[str, List[str]]], model: str, output_file: str) -> Dict[str, str]:
    """
    Main function that generates summaries for all parsed documents.

    Args:
        parsed_docs: Dictionary mapping variable names to document structure
        model: Model to use for summarization ("debug" or "claude")
        output_file: Path to output JavaScript file

    Returns:
        Dictionary mapping variable names to their summaries
    """
    if not parsed_docs:
        print("No documents to summarize.")
        return {}

    summaries = {}

    for var_name, parsed_doc in parsed_docs.items():
        try:
            summary = summarize(model, parsed_doc)
            summaries[var_name] = summary
            print(f"Summarized: {var_name}")

        except Exception as e:
            print(f"🚨 Failed to summarize {var_name}: {e}")
            # Skip this file - don't include it in summaries
            continue

    if summaries:
        # Format and store results
        js_content = format_results(summaries)
        store_results(js_content, output_file)
        print(f"Successfully generated {len(summaries)} summaries")
    else:
        print("🚨 No summaries generated due to errors")

    return summaries


if __name__ == "__main__":
    # Example usage
    sample_docs = {
        "getting_started": "This guide helps you get started with our platform...",
        "api_reference": "The API provides endpoints for managing resources..."
    }

    summaries = generate_summaries(sample_docs, "debug", "test_summaries.js")
    print(f"Returned summaries: {summaries}")
    # File also written to test_summaries.js for Docusaurus
