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
    """
    exclude_config = exclude_config or {}

    # Step 1: Get files based on git status
    if last_commit is None:
        # Get all markdown files if no commit specified
        all_files = get_all_markdown_files(directory)
    else:
        # Get only changed files since commit
        all_files = get_git_changed_files(directory, last_commit)

    # Step 2: Apply exclusion filters
    filtered_files = filter_excluded_files(all_files, exclude_config, directory)

    return filtered_files


def parse_doc(filepath: str) -> str:
    """
    Parse content from an individual Markdown document.

    Args:
        filepath: Path to the markdown file

    Returns:
        String containing all document content
    """
    try:
        analyzer = MarkdownAnalyzer(filepath)
        paragraphs = analyzer.identify_paragraphs()

        # Convert paragraphs to a single string
        # Assuming paragraphs is a list of paragraph objects with text content
        content_parts = []
        for paragraph in paragraphs:
            # Handle different possible paragraph object structures
            if hasattr(paragraph, 'text'):
                content_parts.append(paragraph.text)
            elif hasattr(paragraph, 'content'):
                content_parts.append(paragraph.content)
            elif isinstance(paragraph, str):
                content_parts.append(paragraph)
            else:
                # Try to convert to string as fallback
                content_parts.append(str(paragraph))

        # Join all content with spaces and clean up whitespace
        full_content = ' '.join(content_parts)

        # Remove excessive whitespace and normalize
        import re
        full_content = re.sub(r'\s+', ' ', full_content).strip()

        return full_content

    except Exception as e:
        raise RuntimeError(f"{e}")


def parse_markdown_files(directory: str, last_commit: Optional[str], config_path: str) -> Dict[str, str]:
    """
    Parse all changed Markdown files and return content dictionary.

    Args:
        directory: Directory to scan for markdown files
        last_commit: Git commit hash to compare against (None for all files)
        config_path: Path to the JSON configuration file (for saving updates)

    Returns:
        Dictionary mapping variable names to document content
        Example: {
            "getting_started": "This guide covers the basics of...",
            "api_reference": "The API provides endpoints for..."
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
            content = parse_doc(filepath)
            content_dict[variable_name] = content
            print(f"Parsed: {filepath} -> {variable_name}")

        except Exception as e:
            print(f"🚨 Error parsing {filepath} -- {e}")
            continue

    # Update config with current commit hash for next run
    current_commit = get_current_commit_hash()
    config['commit'] = current_commit
    save_config(config_path, config)

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
        for var_name, content in results.items():
            print(f"  {var_name}: {len(content)} characters")
    except Exception as e:
        print(f"Error: {e}")
