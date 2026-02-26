"""
Meta description management for docdigest.
Handles updating frontmatter in Markdown files and posting PR suggestions.
"""

import os
import re
import json
from typing import Dict, List, Optional, Tuple
import requests
from .file_utils import get_all_markdown_files, get_variable_name, should_exclude_file
from .config import load_config
from .git_utils import run_git_command


def get_pr_number() -> Optional[int]:
    """
    Get PR number from GitHub Actions environment.

    Returns:
        PR number if in PR context, None otherwise
    """
    # Check for workflow_dispatch input first
    event_path = os.environ.get('GITHUB_EVENT_PATH')
    if event_path and os.path.exists(event_path):
        try:
            with open(event_path) as f:
                event_data = json.load(f)
                # Check for workflow_dispatch inputs
                if 'inputs' in event_data and 'pr_number' in event_data['inputs']:
                    return int(event_data['inputs']['pr_number'])
                # Check for automatic pull_request event
                if 'pull_request' in event_data:
                    return event_data['pull_request']['number']
        except Exception:
            pass

    # GitHub Actions sets GITHUB_REF for PR events
    # Format: refs/pull/123/merge
    github_ref = os.environ.get('GITHUB_REF', '')
    match = re.search(r'refs/pull/(\d+)/merge', github_ref)
    if match:
        return int(match.group(1))

    return None


def get_repo_info() -> Tuple[str, str]:
    """
    Get repository owner and name from environment or git remote.

    Returns:
        Tuple of (owner, repo_name)

    Raises:
        RuntimeError: If repository info cannot be determined
    """
    # Try environment variable first (GitHub Actions)
    github_repo = os.environ.get('GITHUB_REPOSITORY')
    if github_repo and '/' in github_repo:
        owner, repo = github_repo.split('/', 1)
        return owner, repo

    # Fall back to parsing git remote
    success, stdout, _ = run_git_command(['git', 'remote', 'get-url', 'origin'])
    if not success:
        raise RuntimeError("Could not determine repository from git remote")

    remote_url = stdout.strip()

    # Parse different remote URL formats:
    # - https://github.com/owner/repo.git
    # - git@github.com:owner/repo.git
    # - https://github.com/owner/repo
    match = re.search(r'github\.com[:/]([^/]+)/([^/\.]+)', remote_url)
    if match:
        return match.group(1), match.group(2)

    raise RuntimeError(f"Could not parse GitHub repository from remote URL: {remote_url}")


def get_pr_changed_files(owner: str, repo: str, pr_number: int) -> List[str]:
    """
    Get list of files changed in a PR from GitHub API.

    Args:
        owner: Repository owner
        repo: Repository name
        pr_number: Pull request number

    Returns:
        List of file paths changed in the PR (relative to repo root)

    Raises:
        RuntimeError: If GitHub token not set or API call fails
    """
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        raise RuntimeError("GITHUB_TOKEN environment variable not set.")

    pr_files_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        files_response = requests.get(pr_files_url, headers=headers)
        files_response.raise_for_status()
        pr_files = files_response.json()
        # Return list of file paths (filenames)
        return [f['filename'] for f in pr_files]
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to get PR files: {e}")


def parse_frontmatter(filepath: str) -> Optional[Dict]:
    """
    Parse frontmatter from a Markdown file.

    Args:
        filepath: Path to the Markdown file

    Returns:
        Dictionary with:
        - 'lines': List of all file lines
        - 'frontmatter_start': Line index of opening --- (usually 0)
        - 'frontmatter_end': Line index of closing ---
        - 'description_line': Line index of description field, or None if not found
        - 'description_value': Current description value if found, None otherwise
        - 'insert_after_line': Suggested line index to insert description (after id/title/sidebar_label)
        Returns None if no valid frontmatter found
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Find frontmatter boundaries
        if not lines or not lines[0].strip().startswith('---'):
            return None

        frontmatter_end = None
        for i in range(1, len(lines)):
            if lines[i].strip().startswith('---'):
                frontmatter_end = i
                break

        if frontmatter_end is None:
            return None

        # Look for existing description field
        description_line = None
        description_value = None
        description_pattern = r'^description:\s*(.*)$'

        for i in range(1, frontmatter_end):
            match = re.match(description_pattern, lines[i])
            if match:
                description_line = i
                description_value = match.group(1).strip().strip('"').strip("'")
                break

        # Find where to insert description if it doesn't exist
        # Preferred order: after id, title, or sidebar_label (whichever comes last)
        insert_after_line = 0  # After opening --- by default
        for i in range(1, frontmatter_end):
            if re.match(r'^(id|title|sidebar_label):', lines[i]):
                insert_after_line = i

        return {
            'lines': lines,
            'frontmatter_start': 0,
            'frontmatter_end': frontmatter_end,
            'description_line': description_line,
            'description_value': description_value,
            'insert_after_line': insert_after_line
        }

    except Exception as e:
        print(f"⚠️  Error parsing frontmatter in {filepath}: {e}")
        return None


def update_frontmatter_description(filepath: str, description: str) -> bool:
    """
    Update or add description field in a Markdown file's frontmatter.

    Args:
        filepath: Path to the Markdown file
        description: Meta description to add/update

    Returns:
        True if file was modified, False if unchanged or error
    """
    try:
        fm = parse_frontmatter(filepath)
        if fm is None:
            raise RuntimeError(f"No frontmatter found in {filepath}")

        lines = fm['lines']
        description_line = fm['description_line']
        escaped_description = description.replace('"', '\\"')
        new_description_line = f'description: "{escaped_description}"\n'

        # Check if already has this exact description
        if description_line is not None:
            if lines[description_line].strip() == new_description_line.strip():
                return False  # No change needed

            # Replace existing description
            lines[description_line] = new_description_line
        else:
            # Insert new description after preferred fields
            insert_at = fm['insert_after_line'] + 1
            lines.insert(insert_at, new_description_line)

        # Write back to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        return True

    except Exception as e:
        raise RuntimeError(f"Failed to update {filepath}: {e}")


def get_description_line_for_github(filepath: str) -> Optional[tuple[int, bool]]:
    """
    Get the line number where description should appear for GitHub PR suggestions.

    Args:
        filepath: Path to the Markdown file

    Returns:
        Tuple of (line_number, description_exists) or None if no frontmatter
        line_number: 1-indexed line number for GitHub API
        description_exists: True if description field already exists
    """
    fm = parse_frontmatter(filepath)
    if fm is None:
        return None

    if fm['description_line'] is not None:
        # Description exists, return its line (1-indexed)
        return (fm['description_line'] + 1, True)
    else:
        # Description doesn't exist, return where to insert (1-indexed)
        # insert_after_line is 0-indexed, so +1 gives us the line after it, +1 again for GitHub's 1-indexing
        return (fm['insert_after_line'] + 2, False)


def update_markdown_meta(meta_descriptions: Dict[str, str], config_path: str) -> None:
    """
    Update frontmatter description fields in Markdown files.

    Args:
        meta_descriptions: Dictionary mapping variable names to meta descriptions
        config_path: Path to configuration file
    """
    # Load configuration
    config = load_config(config_path)
    directory = config['directory']
    exclude_config = config.get('exclude', {})

    # Get all markdown files
    markdown_files = get_all_markdown_files(directory)

    if not markdown_files:
        print("No markdown files found to update.")
        return

    updated_count = 0

    # Process each file that has a meta description
    for filepath in markdown_files:
        variable_name = get_variable_name(filepath, directory)

        # Skip if no meta description for this file
        if variable_name not in meta_descriptions:
            continue

        # Skip excluded files
        if should_exclude_file(filepath, exclude_config, directory):
            continue

        try:
            description = meta_descriptions[variable_name]
            was_updated = update_frontmatter_description(filepath, description)

            if was_updated:
                print(f"✅ Updated meta: {filepath}")
                updated_count += 1

        except Exception as e:
            print(f"🚨 Error updating {filepath}: {e}")

    print(f"\n  • Files updated: {updated_count}/{len(meta_descriptions)}")


def post_pr_suggestions(
    meta_descriptions: Dict[str, str],
    owner: str,
    repo: str,
    pr_number: int,
    config_path: str,
    pr_changed_files: set
) -> None:
    """
    Post meta description suggestions as a PR comment.

    Args:
        meta_descriptions: Dictionary mapping variable names to meta descriptions
        owner: Repository owner
        repo: Repository name
        pr_number: Pull request number
        config_path: Path to configuration file
        pr_changed_files: Set of file paths changed in the PR (relative to repo root)

    Raises:
        RuntimeError: If GitHub token not set or API call fails
    """
    # Check for GitHub token
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        raise RuntimeError("GITHUB_TOKEN environment variable not set. Please set it to post PR comments.")

    # Load configuration
    config = load_config(config_path)
    directory = config['directory']
    exclude_config = config.get('exclude', {})

    # Build comment body with suggestions for PR files
    suggestions = []
    markdown_files = get_all_markdown_files(directory)

    for filepath in markdown_files:
        # Get variable name for this file
        variable_name = get_variable_name(filepath, directory)

        # Skip if no meta description for this file
        if variable_name not in meta_descriptions:
            continue

        # Skip excluded files
        if should_exclude_file(filepath, exclude_config, directory):
            continue

        # Get path relative to repository root
        abs_filepath = os.path.abspath(filepath)
        success, git_root, _ = run_git_command(['git', 'rev-parse', '--show-toplevel'])
        if success:
            relative_path = os.path.relpath(abs_filepath, git_root.strip())
        else:
            relative_path = os.path.relpath(filepath, directory)

        # Only include files that are in the PR diff
        if relative_path not in pr_changed_files:
            continue

        description = meta_descriptions[variable_name]
        char_count = len(description)

        suggestions.append(f"### 📄 `{relative_path}`\n\n```yaml\ndescription: \"{description}\"\n```\n*{char_count} characters*\n")

    if not suggestions:
        print("No suggestions to post (no PR files have meta descriptions)")
        return

    # Build comment body
    comment_body = "## 🤖 Meta description suggestions\n\n"
    comment_body += "Here are meta descriptions for the files in this PR. Check any trademark (®) and product name requirements.\n\n"
    comment_body += "\n".join(suggestions)
    comment_body += "\n---\n*Generated by docdigest*"

    # Post comment to PR
    comment_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        response = requests.post(comment_url, headers=headers, json={"body": comment_body})
        response.raise_for_status()

        html_url = response.json().get('html_url', '')
        print(f"✅ Posted meta description suggestions to PR #{pr_number}")
        if html_url:
            print(f"   View at: {html_url}")

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to post PR comment: {e}")


if __name__ == "__main__":
    # Example usage
    sample_meta = {
        "getting_started": "Learn how to quickly set up and configure our platform with step-by-step instructions and comprehensive guides.",
        "api_reference": "Explore our complete API reference with detailed endpoint documentation, authentication methods, and code examples."
    }

    # Update local files
    update_markdown_meta(sample_meta, "docdigest_config.json")
