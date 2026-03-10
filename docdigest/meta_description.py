"""
AI meta description generation functionality for docdigest.
Generates SEO-optimized meta descriptions for documentation content.
"""

from typing import Dict, List
import os
import time
import anthropic

# Claude model version - update when new versions are released
CLAUDE_MODEL = "claude-sonnet-4-5-20250929"

# Claude Sonnet 4.5 pricing (per million tokens)
CLAUDE_INPUT_PRICE = 3.00  # $3 per 1M input tokens
CLAUDE_OUTPUT_PRICE = 15.00  # $15 per 1M output tokens

# Token limits
MAX_OUTPUT_TOKENS = 60  # Max tokens for meta description output

# Token estimation
WORDS_TO_TOKENS_RATIO = 1.3  # Approximate ratio for token estimation

# Global prompt for meta description generation
META_DESCRIPTION_PROMPT = """
You are an SEO expert writing meta descriptions for technical documentation.

Create a compelling meta description (150-160 characters) that:
- Summarizes the page's main value proposition
- Uses action-oriented language (e.g., "Learn", "Discover", "Explore")
- Naturally incorporates relevant keywords
- Entices users to click from search results
- Uses clear, accessible language
- Focuses on benefits to the reader

Ensure the meta descriptions meet these requirements:
- The description MUST be grammatically correct with proper punctuation and article use.
- The entire description MUST contain 160 characters or fewer.
- Each sentence in the description MUST contain 15 words or fewer.

{supplement}

**Content to summarize:**
{content}

**Document headers:**
{headers}

Provide ONLY the meta description text, nothing else. No quotes, no preamble, just the description.
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


def estimate_meta_costs(parsed_docs: Dict[str, Dict[str, List[str]]], llm: str) -> None:
    """
    Estimate and display costs for generating meta descriptions.

    Args:
        parsed_docs: Dictionary mapping variable names to document structure
        llm: LLM to use ("none" or "claude")
    """
    print(f"🧮 Cost estimation for meta descriptions")

    num_docs = len(parsed_docs)
    print(f"  • Documents to process: {num_docs}")

    if llm == "none":
        print(f"  • Cost: $0.00 (dry run mode uses no API)")
        return

    if num_docs == 0:
        print(f"  • Cost: $0.00 (no documents to process)")
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

    print(f"  • Estimated input tokens: {total_input_tokens:,}")
    print(f"  • Estimated output tokens: {total_output_tokens:,} ({MAX_OUTPUT_TOKENS} tokens per description)")
    print(f"  • Estimated cost: ${estimated_cost:.4f}")
    print(f"\n  (Input: ${CLAUDE_INPUT_PRICE}/M tokens, Output: ${CLAUDE_OUTPUT_PRICE}/M tokens)")


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


def generate_meta_dry_run(parsed_doc: Dict[str, List[str]]) -> str:
    """
    Generate dry run meta description for testing.

    Args:
        parsed_doc: Dictionary with "headers" and "paragraphs" lists

    Returns:
        Dry run meta description string
    """
    header_count = len(parsed_doc.get("headers", []))

    # Count total words in paragraphs
    word_count = 0
    for paragraph in parsed_doc.get("paragraphs", []):
        word_count += len(paragraph.split())

    return f"Dry run meta description. Headers: {header_count}, Words: {word_count}"


def generate_meta_claude(parsed_doc: Dict[str, List[str]], supplement_text: str = "") -> tuple[str, int, int]:
    """
    Generate meta description using Claude API.

    Args:
        parsed_doc: Dictionary with "headers" and "paragraphs" lists
        supplement_text: Formatted supplement text to include in prompt

    Returns:
        Tuple of (meta_description: str, input_tokens: int, output_tokens: int)

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

    # Use the global prompt template with supplement
    prompt = META_DESCRIPTION_PROMPT.format(
        headers=headers_text,
        content=content_text,
        supplement=supplement_text
    )

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

            # Extract meta description and token usage
            meta_description = message.content[0].text.strip()
            input_tokens = message.usage.input_tokens
            output_tokens = message.usage.output_tokens

            return meta_description, input_tokens, output_tokens

        except anthropic.RateLimitError as e:
            # Rate limit - retry with exponential backoff
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
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


def generate_meta(llm: str, parsed_doc: Dict[str, List[str]] = None, supplement_text: str = "") -> tuple[str, int, int]:
    """
    Generate a meta description using the specified LLM.

    Args:
        llm: LLM to use ("none" or "claude")
        parsed_doc: Dictionary with "headers" and "paragraphs" lists
        supplement_text: Formatted supplement text (only used for claude, ignored for "none")

    Returns:
        Tuple of (meta_description, input_tokens, output_tokens)
        For dry run mode, tokens are 0

    Raises:
        ValueError: If unknown LLM specified
    """
    if llm == "none":
        meta_description = generate_meta_dry_run(parsed_doc)
        return meta_description, 0, 0
    elif llm == "claude":
        return generate_meta_claude(parsed_doc, supplement_text)
    else:
        raise ValueError(f"Unknown LLM: {llm}")


def generate_meta_descriptions(
    parsed_docs: Dict[str, Dict[str, List[str]]],
    llm: str,
    supplement_text: str = ""
) -> Dict[str, str]:
    """
    Main function that generates meta descriptions for all parsed documents.

    Args:
        parsed_docs: Dictionary mapping variable names to document structure
        llm: LLM to use ("none" or "claude")
        supplement_text: Formatted supplement text to include in prompts

    Returns:
        Dictionary mapping variable names to their meta descriptions
    """
    if not parsed_docs:
        print("No documents to generate meta descriptions for.")
        return {}

    meta_descriptions = {}
    total_input_tokens = 0
    total_output_tokens = 0

    for var_name, parsed_doc in parsed_docs.items():
        try:
            meta, input_tokens, output_tokens = generate_meta(llm, parsed_doc, supplement_text)
            meta_descriptions[var_name] = meta
            total_input_tokens += input_tokens
            total_output_tokens += output_tokens
            print(f"Generated meta: {var_name} ({len(meta)} chars)")

        except Exception as e:
            print(f"🚨 Failed to generate meta for {var_name}: {e}")
            # Skip this file - don't include it in meta_descriptions
            continue

    # Display total token usage and cost
    if meta_descriptions:
        total_cost = calculate_cost(total_input_tokens, total_output_tokens)
        print(f"  • Total input tokens: {total_input_tokens:,}")
        print(f"  • Total output tokens: {total_output_tokens:,}")
        print(f"  • Total cost: ${total_cost:.4f}")

    return meta_descriptions


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

    meta_descriptions = generate_meta_descriptions(sample_docs, "", "")
    print(f"\nGenerated meta descriptions: {meta_descriptions}")
