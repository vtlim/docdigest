"""
Import processing functionality for docdigest.
Modifies Markdown files to add/remove import statements and summary UI components.
"""

import os
import re
from typing import Dict, List, Optional
from .file_utils import get_all_markdown_files, should_exclude_file, filename_to_variable_name
from .config import load_config


def convert_output_file_to_import_path(output_file: str) -> str:
    """
    Convert output file path to Docusaurus import path.

    Args:
        output_file: Path like "static/js/summaries.js"

    Returns:
        Docusaurus import path like "@site/static/js/summaries.js"
    """
    # Ensure path starts with @site/
    if not output_file.startswith("@site/"):
        return f"@site/{output_file}"
    return output_file


def extract_frontmatter_and_content(file_content: str) -> tuple[str, str, str]:
    """
    Extract frontmatter and content from markdown file.

    Args:
        file_content: Full markdown file content

    Returns:
        Tuple of (frontmatter_block, content_after_frontmatter, full_remaining_content)
    """
    # Match frontmatter pattern: starts with ---, content, ends with ---
    frontmatter_pattern = r'^(---\s*\n.*?\n---\s*\n)(.*?)$'
    match = re.match(frontmatter_pattern, file_content, re.DOTALL)

    if match:
        frontmatter = match.group(1)
        remaining_content = match.group(2)
        return frontmatter, remaining_content, remaining_content
    else:
        # No frontmatter found - this shouldn't happen based on assumptions
        return "", file_content, file_content


def has_existing_summary_component(content: str, variable_name: str) -> bool:
    """
    Check if content already has the summary component with the exact variable name.

    Args:
        content: Markdown content (after frontmatter)
        variable_name: Specific variable name to look for

    Returns:
        True if summary component exists with this exact variable name, False otherwise
    """
    # Check for import statement with exact variable name
    import_pattern = rf'import\s+{{\s*{variable_name}\s*}}\s+from\s+["\'][^"\']*summaries\.js["\']'
    has_import = bool(re.search(import_pattern, content))

    # Check for details component with the exact variable reference
    details_pattern = rf'<details[^>]*>.*?<summary>Summary</summary>.*?{{{variable_name}}}.*?This summary was generated using AI.*?</details>'
    has_details = bool(re.search(details_pattern, content, re.DOTALL))

    return has_import and has_details


def remove_existing_summary_components(content: str) -> str:
    """
    Remove any existing import and summary components from content.

    Args:
        content: Markdown content (after frontmatter)

    Returns:
        Content with any existing summary components removed
    """
    # Remove any import statement from summaries.js
    import_pattern = r'^import\s+\{[^}]+\}\s+from\s+["\'][^"\']*summaries\.js["\']\s*\n*'
    content = re.sub(import_pattern, '', content, flags=re.MULTILINE)

    # Remove any summary details block with our AI disclaimer signature
    details_pattern = r'<details[^>]*>.*?<summary>Summary</summary>.*?This summary was generated using AI.*?</details>\s*\n*'
    content = re.sub(details_pattern, '', content, flags=re.DOTALL)

    # Clean up multiple consecutive newlines
    content = re.sub(r'\n{3,}', '\n\n', content)

    return content


def create_summary_component(variable_name: str, import_path: str) -> str:
    """
    Create the import statement and summary UI component.

    Args:
        variable_name: JavaScript variable name for the summary
        import_path: Docusaurus import path

    Returns:
        Formatted import and component string
    """
    component = f'''import {{{variable_name}}} from "{import_path}"


<details open>
<summary>Summary</summary>

{{{variable_name}}}

<br/><br/>
<span className="small-font">
This summary was generated using AI.
Check important info for mistakes.
</span>

</details>

'''
    return component


def process_markdown_file(filepath: str, variable_name: str, has_summary: bool, import_path: str) -> bool:
    """
    Process a single markdown file to add/remove summary components.

    Args:
        filepath: Path to the markdown file
        variable_name: JavaScript variable name for this file
        has_summary: Whether this file has a summary in the summaries dict
        import_path: Docusaurus import path for summaries

    Returns:
        True if file was modified successfully, False if skipped due to error
    """
    try:
        # Read file content
        with open(filepath, 'r', encoding='utf-8') as file:
            original_content = file.read()

        # Extract frontmatter and content
        frontmatter, after_frontmatter, _ = extract_frontmatter_and_content(original_content)

        if not frontmatter:
            print(f"🚨 No frontmatter found in {filepath}, skipping")
            return False

        # Check current state
        currently_has_component = has_existing_summary_component(after_frontmatter, variable_name)

        # Determine if we need to make changes
        needs_component = has_summary
        needs_changes = currently_has_component != needs_component

        if not needs_changes:
            print(f"⚪ No changes needed: {filepath}")
            return True

        # Make changes
        if needs_component:
            # Remove existing (if any) and add new component
            cleaned_content = remove_existing_summary_components(after_frontmatter)
            summary_component = create_summary_component(variable_name, import_path)
            new_content = frontmatter + summary_component + cleaned_content
            action = "➕ Added import"
        else:
            # Remove existing component
            cleaned_content = remove_existing_summary_components(after_frontmatter)
            new_content = frontmatter + cleaned_content
            action = "⛔ Removed import"

        # Write the file
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(new_content)

        print(f"{action}: {filepath}")
        return True

    except Exception as e:
        print(f"🚨 Error processing {filepath}: {e}")
        return False


def update_markdown_imports(summaries: Dict[str, str], config_path: str) -> None:
    """
    Update all markdown files with appropriate import statements and summary components.

    Args:
        summaries: Dictionary mapping variable names to summary content
        config_path: Path to configuration file
    """
    # Load configuration
    config = load_config(config_path)
    directory = config['directory']  # required field, will raise KeyError if missing
    output_file = config.get('output_file', 'summaries.js')  # optional with default
    exclude_config = config.get('exclude', {})

    # Convert output file to import path
    import_path = convert_output_file_to_import_path(output_file)

    print(f"Updating markdown imports to {import_path})...")

    # Get all markdown files in directory
    all_markdown_files = get_all_markdown_files(directory)

    # Filter out excluded files
    markdown_files = []
    for filepath in all_markdown_files:
        if not should_exclude_file(filepath, exclude_config, directory):
            markdown_files.append(filepath)

    if not markdown_files:
        print("No markdown files found to process.")
        return

    processed_count = 0
    modified_count = 0

    # Process each markdown file
    for filepath in markdown_files:
        # Get variable name for this file
        variable_name = filename_to_variable_name(filepath, directory)

        # Check if this file has a summary
        has_summary = variable_name in summaries

        # Process the file
        success = process_markdown_file(filepath, variable_name, has_summary, import_path)

        if success:
            processed_count += 1
            if has_summary:
                modified_count += 1

    print(f"📊 Import processing complete:")
    print(f"  • Files processed: {processed_count}/{len(markdown_files)}")
    print(f"  • Files with summaries added: {modified_count}")
    print(f"  • Files with summaries removed: {processed_count - modified_count}")


if __name__ == "__main__":
    # Example usage
    sample_summaries = {
        "getting_started": "This guide covers the basics of getting started...",
        "api_reference": "The API reference provides detailed information..."
    }

    update_markdown_imports(sample_summaries, "docdigest_config.json")
