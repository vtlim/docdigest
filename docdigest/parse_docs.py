"""
Markdown parsing functionality for docdigest.
Uses mrkdwn_analysis to extract content from Markdown files and tracks changes via git commits.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from mrkdwn_analysis import MarkdownAnalyzer


def load_config(config_path: str) -> Dict:
    """
    Load configuration from JSON file.

    Args:
        config_path: Path to the JSON configuration file

    Returns:
        Configuration dictionary with 'directory' and 'commit' keys
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in configuration file: {e}")


def save_config(config_path: str, config: Dict) -> None:
    """
    Save configuration to JSON file.

    Args:
        config_path: Path to the JSON configuration file
        config: Configuration dictionary to save
    """
    with open(config_path, 'w', encoding='utf-8') as file:
        json.dump(config, file, indent=2)


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
        raise RuntimeError("Failed to get current git commit hash")


def get_changed_files(directory: str, since_commit: Optional[str] = None) -> List[str]:
    """
    Get list of changed Markdown files in directory since specified commit.

    Args:
        directory: Directory to scan for files
        since_commit: Git commit hash to compare against (None for all files)

    Returns:
        List of file paths that have changed
    """
    if since_commit is None:
        # Return all markdown files if no commit specified
        markdown_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.md'):
                    markdown_files.append(os.path.join(root, file))
        return markdown_files

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
        raise RuntimeError(f"Failed to get changed files since commit {since_commit}")


def get_files(config_path: str) -> List[str]:
    """
    Get list of changed docs from a specified directory based on the commit difference.

    Args:
        config_path: Path to the JSON configuration file

    Returns:
        List of file paths that have changed since the last recorded commit
    """
    config = load_config(config_path)
    directory = config.get('directory', '')
    last_commit = config.get('commit')

    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory not found: {directory}")

    return get_changed_files(directory, last_commit)


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
        raise RuntimeError(f"Failed to parse document {filepath}: {e}")


def parse_markdown_files(config_path: str) -> Dict[str, str]:
    """
    Parse all changed Markdown files and return content dictionary.

    Args:
        config_path: Path to the JSON configuration file

    Returns:
        Dictionary mapping variable names to document content
        Example: {
            "getting_started": "This guide covers the basics of...",
            "api_reference": "The API provides endpoints for..."
        }
    """
    config = load_config(config_path)
    directory = config['directory']

    # Get list of changed files
    changed_files = get_files(config_path)

    if not changed_files:
        print("No changed Markdown files found.")
        return {}

    # Parse each file and build content dictionary
    content_dict = {}

    for filepath in changed_files:
        try:
            variable_name = filename_to_variable_name(filepath, directory)
            content = parse_doc(filepath)
            content_dict[variable_name] = content
            print(f"Parsed: {filepath} -> {variable_name}")

        except Exception as e:
            print(f"Error parsing {filepath}: {e}")
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
        results = parse_markdown_files(config_path)
        print(f"\nParsed {len(results)} files:")
        for var_name, content in results.items():
            print(f"  {var_name}: {len(content)} characters")
    except Exception as e:
        print(f"Error: {e}")
