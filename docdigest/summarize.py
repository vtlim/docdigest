"""
AI summarization functionality for docdigest.
Generates short text summaries for documentation content and formats them as JavaScript modules.
"""

from typing import Dict, List, Optional
import os
import time
import anthropic

# Claude model version - update when new versions are released
CLAUDE_MODEL = "claude-sonnet-4-5-20250929"

# Claude Sonnet 4.5 pricing (per million tokens)
CLAUDE_INPUT_PRICE = 3.00  # $3 per 1M input tokens
CLAUDE_OUTPUT_PRICE = 15.00  # $15 per 1M output tokens

# Token estimation and limits
WORDS_TO_TOKENS_RATIO = 1.3  # Approximate ratio for token estimation
MAX_OUTPUT_TOKENS = 100  # Max tokens for summary output

# Global prompt for summarization
SUMMARIZATION_PROMPT = """
You are a technical documentation summarizer.
Your task is to create concise, informative summaries for documentation pages.
The summary will be displayed in an expandable section at the top of the documentation pages.

**Instructions:**
- For the provided content, summarize the main purpose and key information
- Use the provided headers to understand the page structure, but don't give them disproportionate weight in the summary
- Focus on what the reader will learn or accomplish
- Write it for an audience of developers or technical users
- Use plain text between 25-35 words and no special formatting
- Use clear, accessible language that matches the original tone
- Avoid unnecessary jargon unless it's essential to understanding
- Make the summary standalone - someone should understand the page's value without reading the full content

**Content to summarize:**
{content}

**Document headers:**
{headers}

Provide only the summary text, nothing else.
"""

# JavaScript module header comment
JS_MODULE_HEADER = """/*
Summaries for each topic, matched by filename
*/

"""


def estimate_token_count(parsed_doc: Dict[str, List[str]]) -> int:
    """
    Estimate token count for a parsed document.

    Args:
        parsed_doc: Dictionary with "headers" and "paragraphs" lists

    Returns:
        Estimated token count
    """
    # Count words in headers and paragraphs
    total_words = 0

    for header in parsed_doc.get("headers", []):
        total_words += len(header.split())

    for paragraph in parsed_doc.get("paragraphs", []):
        total_words += len(paragraph.split())

    # Estimate tokens (rough approximation)
    estimated_tokens = int(total_words * WORDS_TO_TOKENS_RATIO)

    return estimated_tokens


def calculate_cost(input_tokens: int, output_tokens: int) -> float:
    """
    Calculate cost in dollars based on token usage.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Cost in dollars
    """
    input_cost = (input_tokens / 1_000_000) * CLAUDE_INPUT_PRICE
    output_cost = (output_tokens / 1_000_000) * CLAUDE_OUTPUT_PRICE
    return input_cost + output_cost


def estimate_costs(parsed_docs: Dict[str, Dict[str, List[str]]], model: str) -> None:
    """
    Estimate and display costs for summarizing documents.

    Args:
        parsed_docs: Dictionary mapping variable names to document structure
        model: Model to use ("debug" or "claude")
    """
    print(f"🧮 Dry-run mode: Cost estimation")

    num_docs = len(parsed_docs)
    print(f"  • Documents to summarize: {num_docs}")

    if model == "debug":
        print(f"  • Cost: $0.00 (debug mode uses no API)")
        return

    # Estimate tokens for all docs
    total_input_tokens = 0
    for var_name, parsed_doc in parsed_docs.items():
        estimated_tokens = estimate_token_count(parsed_doc)
        total_input_tokens += estimated_tokens

    # Estimate output tokens (assume MAX_OUTPUT_TOKENS per doc)
    total_output_tokens = num_docs * MAX_OUTPUT_TOKENS

    # Calculate cost
    estimated_cost = calculate_cost(total_input_tokens, total_output_tokens)

    print(f"  • Actual input tokens: {total_input_tokens:,}")
    print(f"  • Estimated output tokens: {total_output_tokens:,} ({MAX_OUTPUT_TOKENS} tokens per summary)")
    print(f"  • Estimated cost: ${estimated_cost:.4f}")
    print(f"\n  (Input: ${CLAUDE_INPUT_PRICE}/M tokens, Output: ${CLAUDE_OUTPUT_PRICE}/M tokens)")


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


def summarize_claude(parsed_doc: Dict[str, List[str]]) -> tuple[str, int, int]:
    """
    Claude summarization with header-aware prompting.

    Args:
        parsed_doc: Dictionary with "headers" and "paragraphs" lists

    Returns:
        Tuple of (summary: str, input_tokens: int, output_tokens: int)

    Raises:
        RuntimeError: If API key not set or API call fails
    """
    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable not set. Please set it to use Claude API.")

    # Prepare content
    headers_text = ", ".join(parsed_doc.get("headers", []))
    content_text = " ".join(parsed_doc.get("paragraphs", []))

    # Use the global prompt template with header emphasis
    prompt = SUMMARIZATION_PROMPT.format(headers=headers_text, content=content_text)

    # Call Claude API with retry logic
    max_retries = 5
    base_delay = 1  # seconds

    for attempt in range(max_retries):
        try:
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=MAX_OUTPUT_TOKENS,
                messages=[{"role": "user", "content": prompt}]
            )

            # Extract summary and token usage
            summary = message.content[0].text.strip()
            input_tokens = message.usage.input_tokens
            output_tokens = message.usage.output_tokens

            return summary, input_tokens, output_tokens

        except anthropic.RateLimitError as e:
            # Rate limit - retry with longer backoff
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)  # Exponential backoff
                print(f"⚠️  Rate limit hit, retrying in {delay}s...")
                time.sleep(delay)
            else:
                raise RuntimeError(f"Rate limit exceeded after {max_retries} retries: {e}")

        except (anthropic.APIConnectionError, anthropic.APITimeoutError) as e:
            # Network errors - retry with exponential backoff
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"⚠️  Network error, retrying in {delay}s...")
                time.sleep(delay)
            else:
                raise RuntimeError(f"Network error after {max_retries} retries: {e}")

        except anthropic.APIStatusError as e:
            # Server errors (5xx) - retry
            if e.status_code >= 500 and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"⚠️  Server error {e.status_code}, retrying in {delay}s...")
                time.sleep(delay)
            else:
                # 4xx errors (except 429) or final retry - don't retry
                raise RuntimeError(f"API error: {e}")

        except Exception as e:
            # Unexpected errors - fail immediately
            raise RuntimeError(f"Unexpected error calling Claude API: {e}")

    raise RuntimeError("Failed to get response from Claude API")


def summarize(model: str, parsed_doc: Dict[str, List[str]] = None) -> tuple[str, int, int]:
    """
    Generate summary using specified model.

    Args:
        model: Model to use ("debug" or "claude")
        parsed_doc: Dictionary with "headers" and "paragraphs" lists (needed for both models)

    Returns:
        Tuple of (summary: str, input_tokens: int, output_tokens: int)
        Input and output count show the costs per each doc
        For debug mode, tokens are 0

    Raises:
        ValueError: If unknown model specified
    """
    if model == "debug":
        summary = summarize_debug(parsed_doc)
        return summary, 0, 0
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
    total_input_tokens = 0
    total_output_tokens = 0

    for var_name, parsed_doc in parsed_docs.items():
        try:
            summary, input_tokens, output_tokens = summarize(model, parsed_doc)
            summaries[var_name] = summary
            total_input_tokens += input_tokens
            total_output_tokens += output_tokens
            print(f"Summarized: {var_name}")

        except Exception as e:
            print(f"🚨 Failed to summarize {var_name}: {e}")
            # Skip this file - don't include it in summaries
            continue

    if summaries:
        # Format and store results
        js_content = format_results(summaries)
        store_results(js_content, output_file)

        # Show summary statistics
        print(f"Summarization complete")
        print(f"  • Documents processed: {len(summaries)}")

        if model == "claude":
            total_cost = calculate_cost(total_input_tokens, total_output_tokens)
            print(f"  • Total input tokens: {total_input_tokens:,}")
            print(f"  • Total output tokens: {total_output_tokens:,}")
            print(f"  • Total cost: ${total_cost:.4f}")
    else:
        print("🚨 No summaries generated due to errors")

    return summaries


if __name__ == "__main__":
    # Example usage
    sample_docs = {
        "getting_started": {
            "headers": ["Getting Started", "Quick Setup"],
            "paragraphs": ["This guide helps you get started with our platform...", "Follow these steps to begin..."]
        },
        "api_reference": {
            "headers": ["API Reference", "Authentication"],
            "paragraphs": ["The API provides endpoints for managing resources...", "Use your API key to authenticate..."]
        }
    }

    summaries = generate_summaries(sample_docs, "debug", "test_summaries.js")
    print(f"Generated summaries: {summaries}")
