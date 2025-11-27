"""
Shared file operations for docdigest.
Contains utilities for file discovery, exclusion checking, and filename processing.
"""

import os
import re
import fnmatch
from typing import Dict, List, Optional


def get_all_markdown_files(directory: str) -> List[str]:
    """
    Get all Markdown files in directory recursively.

    Args:
        directory: Directory to scan for files

    Returns:
        List of all markdown file paths (no exclusions applied)
    """
    markdown_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.md'):
                markdown_files.append(os.path.join(root, file))
    return markdown_files


def should_exclude_file(filepath: str, exclude_config: Dict, base_directory: str) -> bool:
    """
    Check if a file should be excluded from processing based on exclude configuration.
    All exclude patterns are relative to the base_directory.

    Args:
        filepath: Full path to the file
        exclude_config: Exclude configuration dictionary
        base_directory: Base directory to make paths relative to

    Returns:
        True if file should be excluded, False otherwise
    """
    if not exclude_config:
        return False

    # Get relative path from base directory
    try:
        relative_path = os.path.relpath(filepath, base_directory)
    except ValueError:
        # Handle case where paths are on different drives (Windows)
        return False

    # Check exact file matches (relative to base directory)
    exact_files = exclude_config.get('files', [])
    if relative_path in exact_files:
        return True

    # Check pattern matches (relative to base directory)
    patterns = exclude_config.get('patterns', [])
    for pattern in patterns:
        if fnmatch.fnmatch(relative_path, pattern):
            return True

    # Check directory exclusions (relative to base directory)
    directories = exclude_config.get('directories', [])
    for directory in directories:
        # Normalize directory path and ensure it ends with separator
        norm_dir = os.path.normpath(directory)
        if not norm_dir.endswith(os.sep):
            norm_dir += os.sep

        # Check if relative path starts with the excluded directory
        if relative_path.startswith(norm_dir) or relative_path + os.sep == norm_dir:
            return True

    return False


def filter_excluded_files(files: List[str], exclude_config: Dict, base_directory: str) -> List[str]:
    """
    Filter out excluded files from a list based on exclude configuration.

    Args:
        files: List of file paths to filter
        exclude_config: Exclude configuration dictionary
        base_directory: Base directory for relative path calculations

    Returns:
        List of files with excluded ones removed
    """
    if not exclude_config:
        return files

    filtered_files = []
    for filepath in files:
        if not should_exclude_file(filepath, exclude_config, base_directory):
            filtered_files.append(filepath)

    return filtered_files


def extract_frontmatter_and_content(file_content: str) -> tuple[str, str, str]:
    """
    Extract frontmatter and content from markdown file content.

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
        # No frontmatter found
        return "", file_content, file_content


def has_frontmatter(filepath: str) -> bool:
    """
    Check if a Markdown file has YAML frontmatter.

    Args:
        filepath: Path to the markdown file

    Returns:
        True if frontmatter exists, False otherwise
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()

        frontmatter, _, _ = extract_frontmatter_and_content(content)
        return frontmatter != ""
    except Exception:
        return False


def extract_frontmatter_id(filepath: str) -> Optional[str]:
    """
    Extract the 'id' field from YAML frontmatter in a Markdown file.

    Args:
        filepath: Path to the markdown file

    Returns:
        The id value if found, None otherwise
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()

        frontmatter_block, _, _ = extract_frontmatter_and_content(content)

        if not frontmatter_block:
            return None

        # Look for id: value line in the frontmatter content (strip the --- markers)
        frontmatter_content = frontmatter_block.strip().strip('-').strip()

        id_match = re.search(r'^id:\s*(.+)$', frontmatter_content, re.MULTILINE)

        if id_match:
            # Extract and clean the id value (remove quotes if present)
            id_value = id_match.group(1).strip()
            id_value = id_value.strip('"').strip("'")
            return id_value

        return None
    except Exception:
        return None


def get_variable_name(filepath: str, base_directory: str) -> str:
    """
    Get a valid Python/JavaScript variable name for a markdown file.
    First attempts to use the 'id' from YAML frontmatter, falls back to filename.

    Args:
        filepath: Full path to the markdown file
        base_directory: Base directory to make path relative to

    Returns:
        Valid variable name (e.g., "otlp", "send_events_splunk_hec")
    """
    # Try to get id from frontmatter first
    frontmatter_id = extract_frontmatter_id(filepath)

    if frontmatter_id:
        # Get the relative directory of the doc relative to the provided directory
        relative_dir = os.path.dirname(os.path.relpath(filepath, base_directory))
        # Use the id from frontmatter and concatenate with directory location
        name = os.path.join(relative_dir, frontmatter_id)
    else:
        # Get the relative path of doc relative to the provided directory
        relative_path = os.path.relpath(filepath, base_directory)
        # Fall back to filename-based approach
        name = os.path.splitext(relative_path)[0]

    # Replace path separators and hyphens with underscores
    name = name.replace('/', '_').replace('\\', '_').replace('-', '_')

    # Convert to lowercase and remove any remaining invalid characters
    name = ''.join(c.lower() if c.isalnum() or c == '_' else '_' for c in name)

    # Remove consecutive underscores
    name = '_'.join(filter(None, name.split('_')))

    # Ensure it doesn't start with a number
    if name and name[0].isdigit():
        name = f"doc_{name}"

    return name or "unnamed_doc"


def parse_summaries_file(file_path: str) -> Dict[str, str]:
    """
    Parse summaries.js file and extract variable:value pairs.

    Args:
        file_path: Path to summaries.js file

    Returns:
        Dictionary mapping variable names to their summary values
    """
    if not os.path.exists(file_path):
        return {}

    summaries = {}

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                # Match lines like: const variable_name = "summary text";
                if line.strip().startswith('const '):
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        var_name = parts[0].replace('const', '').strip()
                        # Extract value between quotes
                        value_part = parts[1].strip()
                        if '"' in value_part:
                            value = value_part.split('"')[1]
                            summaries[var_name] = value
    except Exception as e:
        print(f"⚠️  Warning: Could not parse summaries file: {e}")
        return {}

    return summaries


if __name__ == "__main__":
    # Example usage
    import json

    # Test file discovery
    files = get_all_markdown_files("docs/")
    print(f"Found {len(files)} markdown files")

    # Test exclusion
    exclude_config = {
        "patterns": ["*/README.md"],
        "files": ["index.md"],
        "directories": ["blog/"]
    }

    filtered = filter_excluded_files(files, exclude_config, "docs/")
    print(f"After exclusions: {len(filtered)} files")

    # Test variable name generation
    for filepath in filtered[:5]:  # Show first 5
        var_name = get_variable_name(filepath, "docs/")
        print(f"  {filepath} -> {var_name}")
