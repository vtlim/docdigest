"""
Markdown parsing functionality for docdigest.
Uses mrkdwn_analysis to extract content from Markdown files and tracks changes via git commits.
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from mrkdwn_analysis import MarkdownAnalyzer
from .config import load_config, save_config
from .file_utils import get_all_markdown_files, should_exclude_file, filter_excluded_files, filename_to_variable_name


def get_current_commit_hash() -> str:
    """
    Get the current git commit hash.

    Returns:
        Current commit hash as string
    """
    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        raise RuntimeError("🚨 Failed to get current git commit hash")


def is_git_repository() -> bool:
    """
    Check if current directory is a git repository.

    Returns:
        True if git repo exists, False otherwise
    """
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_git_changed_files(directory: str, since_commit: str) -> List[str]:


    """
    Get list of changed Markdown files from git since specified commit.

    Args:
        directory: Directory to scan for files
        since_commit: Git commit hash to compare against

    Returns:
        List of changed markdown file paths (no exclusions applied)
    """
    try:
        # Get changed files since the specified commit
        result = subprocess.run(
            ['git', 'diff', '--name-only', f'{since_commit}..HEAD'],
            capture_output=True,
            text=True,
            check=True
        )

        changed_files = result.stdout.strip().split('\n')

        # Filter for markdown files in the specified directory
        markdown_files = []
        for file_path in changed_files:
            if (file_path.endswith('.md') and
                file_path.startswith(directory) and
                os.path.exists(file_path)):
                markdown_files.append(file_path)

        return markdown_files

    except subprocess.CalledProcessError:
        raise RuntimeError(f"🚨 Failed to get changed files since commit {since_commit}")


def get_files_to_process(directory: str, last_commit: Optional[str], exclude_config: Dict = None) -> List[str]:
    """
    Get list of markdown files to process based on git changes and exclusion rules.

    Args:
        directory: Directory to scan for files
        last_commit: Git commit hash to compare against (None for all files)
        exclude_config: Configuration dictionary for files to exclude

    Returns:
        List of file paths to process

    Raises:
        RuntimeError: If commit hash provided but git not available
    """
    exclude_config = exclude_config or {}

    # If commit hash is provided, git must be available
    if last_commit is not None:
        if not is_git_repository():
            raise RuntimeError("Commit hash provided but not in a git repository. Please initialize git or remove commit hash from config.")

    # Step 1: Get files based on git status
    if last_commit is None:
        # No commit hash - get all files (don't require git)
        try:
            all_files = get_all_markdown_files(directory)
        except Exception as e:
            # Fall back to all files if any error
            print(f"⚠️  Warning: Error during file discovery, processing all files: {e}")
            all_files = get_all_markdown_files(directory)
    else:
        # Commit hash provided - git must work
        all_files = get_git_changed_files(directory, last_commit)

    # Step 2: Apply exclusion filters
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

    # Get list of files to process (git changes + exclusions)
    files_to_process = get_files_to_process(directory, last_commit, exclude_config)

    if not files_to_process:
        print("No Markdown files found to process.")
        return {}

    # Parse each file and build content dictionary
    content_dict = {}

    for filepath in files_to_process:
        try:
            variable_name = filename_to_variable_name(filepath, directory)
            parsed_content = parse_doc(filepath)
            content_dict[variable_name] = parsed_content
            print(f"Parsed: {filepath} -> {variable_name}")

        except Exception as e:
            print(f"🚨 Error parsing {filepath} -- {e}")
            continue

    # Update config with current commit hash for next run (only if git available)
    if is_git_repository():
        current_commit = get_current_commit_hash()
        config['commit'] = current_commit
        save_config(config_path, config)
    else:
        # No git repo - don't update commit hash
        print("⚠️  Not in a git repository. Commit hash will not be updated in config.")

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
