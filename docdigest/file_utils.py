"""
Shared file operations for docdigest.
Contains utilities for file discovery, exclusion checking, and filename processing.
"""

import os
import fnmatch
from typing import Dict, List


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


def filename_to_variable_name(filepath: str, base_directory: str) -> str:
    """
    Convert file path to valid Python/JavaScript variable name.

    Args:
        filepath: Full path to the markdown file
        base_directory: Base directory to make path relative to

    Returns:
        Valid variable name (e.g., "ref_s2s", "send_events_splunk_hec")
    """
    # Get relative path from base directory
    relative_path = os.path.relpath(filepath, base_directory)

    # Remove .md extension
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
        var_name = filename_to_variable_name(filepath, "docs/")
        print(f"  {filepath} -> {var_name}")
