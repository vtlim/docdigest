"""
Markdown parsing functionality for docdigest.
Uses mrkdwn_analysis to extract content from Markdown files and tracks changes via git commits.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from mrkdwn_analysis import MarkdownAnalyzer
from .config import load_config, save_config
from .file_utils import get_all_markdown_files, should_exclude_file, filter_excluded_files, get_variable_name, has_frontmatter
from .git_utils import is_git_repository, get_git_changed_files, run_git_command


def get_exclude_config_from_commit(config_path: str, commit_hash: str) -> Optional[Dict]:
    """
    Get the exclude configuration from a specific git commit.

    Args:
        config_path: Path to the config file
        commit_hash: Git commit hash to retrieve from

    Returns:
        Exclude config dict from that commit, or None if not found
    """
    success, stdout, _ = run_git_command(['git', 'show', f'{commit_hash}:{config_path}'])

    if not success:
        return None

    try:
        config_at_commit = json.loads(stdout)
        return config_at_commit.get('exclude', {})
    except json.JSONDecodeError:
        return None


def has_exclude_config_changed(current_exclude: Dict, config_path: str, commit_hash: Optional[str]) -> bool:
    """
    Check if the exclude configuration has changed since the last commit.

    Args:
        current_exclude: Current exclude configuration
        config_path: Path to the config file
        commit_hash: Git commit hash to compare against

    Returns:
        True if config has changed or can't be determined, False if unchanged
    """
    if commit_hash is None:
        # No commit to compare against, assume changed
        return True

    last_exclude = get_exclude_config_from_commit(config_path, commit_hash)

    if last_exclude is None:
        # Couldn't get previous config, assume changed to be safe
        return True

    # Compare as JSON strings for easy comparison
    return json.dumps(current_exclude, sort_keys=True) != json.dumps(last_exclude, sort_keys=True)


def get_files_to_process(directory: str, last_commit: Optional[str], exclude_config: Dict = None, config_path: str = None) -> List[str]:
    """
    Get list of markdown files to process based on git changes and exclusion rules.

    Args:
        directory: Directory to scan for files
        last_commit: Git commit hash to compare against (None for all files)
        exclude_config: Configuration dictionary for files to exclude
        config_path: Path to config file (for checking exclude config changes)

    Returns:
        List of file paths to process

    Raises:
        RuntimeError: If commit hash provided but git not available
    """
    exclude_config = exclude_config or {}

    # Check if exclude config has changed (if we have a commit to compare against)
    exclude_changed = False
    old_exclude_config = None
    if config_path and last_commit:
        old_exclude_config = get_exclude_config_from_commit(config_path, last_commit)
        if old_exclude_config is not None:
            exclude_changed = json.dumps(exclude_config, sort_keys=True) != json.dumps(old_exclude_config, sort_keys=True)

    if exclude_changed:
        print(f"ℹ️  Exclude configuration changed since {last_commit}")

    # If commit hash is provided, git must be available
    if last_commit is not None:
        if not is_git_repository():
            raise RuntimeError("Commit hash provided but not in a git repository. Please initialize git or remove commit hash from config.")

    # Step 1: Get files based on git status or exclude config changes
    if last_commit is None:
        # No commit hash - get all files
        try:
            all_files = get_all_markdown_files(directory)
        except Exception as e:
            # Fall back to all files if any error
            print(f"⚠️  Warning: Error during file discovery, processing all files: {e}")
            all_files = get_all_markdown_files(directory)
    elif exclude_changed and old_exclude_config is not None:
        # Exclude config changed - get changed files PLUS newly included files
        changed_files = get_git_changed_files(directory, last_commit)

        # Get all files to find newly included ones
        all_files = get_all_markdown_files(directory)

        print(f"  • Config change: old exclude = {old_exclude_config}")
        print(f"  • Config change: new exclude = {exclude_config}")

        # Find files that were excluded before but not now
        newly_included_files = []
        for file_path in all_files:
            was_excluded = should_exclude_file(file_path, old_exclude_config, directory)
            is_excluded = should_exclude_file(file_path, exclude_config, directory)

            if was_excluded and not is_excluded:
                newly_included_files.append(file_path)

        # Combine changed files with newly included files (remove duplicates)
        all_files = list(set(changed_files + newly_included_files))
        print(f"Processing {len(all_files)} files")

    else:
        # Commit hash provided and exclude unchanged - only get changed files
        all_files = get_git_changed_files(directory, last_commit)

    # Step 2: Apply current exclusion filters
    filtered_files = filter_excluded_files(all_files, exclude_config, directory)

    return filtered_files


def filter_meaningful_content(paragraphs: List[str]) -> List[str]:
    """
    Filter out technical noise and keep meaningful content for summarization.

    Args:
        paragraphs: List of paragraph strings from markdown analysis

    Returns:
        Filtered list of meaningful paragraph strings
    """
    filtered = []
    for paragraph in paragraphs:
        # Skip import statements
        if paragraph.startswith('import ') and 'from' in paragraph:
            continue
        # Skip JSX variable references
        if paragraph.startswith('{') and paragraph.endswith('}'):
            continue
        # Skip HTML tags
        if paragraph.startswith('<') and paragraph.endswith('>'):
            continue
        # Skip very short fragments
        if len(paragraph.split()) < 3:
            continue

        filtered.append(paragraph)
    return filtered


def parse_doc(filepath: str) -> Dict[str, List[str]]:
    """
    Parse content from an individual Markdown document.

    Args:
        filepath: Path to the markdown file

    Returns:
        Dictionary containing headers and paragraphs:
        {
            "headers": ["Python 3.11", "Performance Details"],
            "paragraphs": ["Let's discover Docusaurus...", "Get started by creating..."]
        }
    """
    try:
        analyzer = MarkdownAnalyzer(filepath)

        # Get both paragraphs and headers
        paragraphs_result = analyzer.identify_paragraphs()
        headers_result = analyzer.identify_headers()

        paragraphs = paragraphs_result.get("Paragraph", [])
        headers_data = headers_result.get("Header", [])

        # Extract header text
        header_texts = [header["text"] for header in headers_data]

        # Filter meaningful paragraphs
        meaningful_paragraphs = filter_meaningful_content(paragraphs)

        return {
            "headers": header_texts,
            "paragraphs": meaningful_paragraphs
        }

    except Exception as e:
        raise RuntimeError(f"{e}")


def parse_markdown_files(directory: str, last_commit: Optional[str], config_path: str) -> Dict[str, Dict[str, List[str]]]:
    """
    Parse all changed Markdown files and return content dictionary.

    Args:
        directory: Directory to scan for markdown files
        last_commit: Git commit hash to compare against (None for all files)
        config_path: Path to the JSON configuration file (for saving updates)

    Returns:
        Dictionary mapping variable names to document structure:
        Example: {
            "getting_started": {
                "headers": ["Getting Started", "Installation"],
                "paragraphs": ["This guide covers...", "First, install..."]
            },
            "api_reference": {
                "headers": ["API Reference", "Authentication"],
                "paragraphs": ["The API provides...", "To authenticate..."]
            }
        }
    """
    # Load config to get exclude configuration
    config = load_config(config_path)
    exclude_config = config.get('exclude', {})

    # Get list of files to process (git changes + exclusions + exclude config changes)
    files_to_process = get_files_to_process(directory, last_commit, exclude_config, config_path)

    if not files_to_process:
        print("No Markdown files changed or newly included.")
        return {}

    # Parse each file and build content dictionary
    content_dict = {}

    for filepath in files_to_process:
        try:
            # Check if file has frontmatter before processing
            if not has_frontmatter(filepath):
                print(f"⚠️  Skipping {filepath}: no frontmatter found")
                continue

            variable_name = get_variable_name(filepath, directory)
            parsed_content = parse_doc(filepath)
            content_dict[variable_name] = parsed_content
            print(f"Parsed: {filepath} -> {variable_name}")

        except Exception as e:
            print(f"🚨 Error parsing {filepath} -- {e}")
            continue

    return content_dict


if __name__ == "__main__":
    # Example usage
    config_path = "docdigest_config.json"

    # Parse files
    try:
        config = load_config(config_path)
        directory = config['directory']
        last_commit = config.get('commit')
        results = parse_markdown_files(directory, last_commit, config_path)
        print(f"\nParsed {len(results)} files:")
        for var_name, parsed_data in results.items():
            header_count = len(parsed_data["headers"])
            paragraph_count = len(parsed_data["paragraphs"])
            print(f"  {var_name}: {header_count} headers, {paragraph_count} paragraphs")
    except Exception as e:
        print(f"Error: {e}")
