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
    # GitHub Actions sets GITHUB_REF for PR events
    # Format: refs/pull/123/merge
    github_ref = os.environ.get('GITHUB_REF', '')
    match = re.search(r'refs/pull/(\d+)/merge', github_ref)
    if match:
        return int(match.group(1))

    # Alternative: Check GITHUB_EVENT_PATH
    event_path = os.environ.get('GITHUB_EVENT_PATH')
    if event_path and os.path.exists(event_path):
        try:
            with open(event_path) as f:
                event_data = json.load(f)
                if 'pull_request' in event_data:
                    return event_data['pull_request']['number']
        except Exception:
            pass

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


def update_frontmatter_description(filepath: str, description: str) -> bool:
    """
    Update or add description field in a Markdown file's frontmatter.

    Args:
        filepath: Path to the Markdown file
        description: Meta description to add/update

    Returns:
        True if file was modified, False if unchanged or error

    Raises:
        RuntimeError: If file cannot be processed
    """
    try:
        # Read file
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Match frontmatter (YAML between --- delimiters)
        frontmatter_pattern = r'^---\n(.*?)\n---\n(.*)$'
        match = re.match(frontmatter_pattern, content, re.DOTALL)

        if not match:
            raise RuntimeError(f"No frontmatter found in {filepath}")

        frontmatter = match.group(1)
        body = match.group(2)

        # Check if description already exists
        description_pattern = r'^description:\s*["\']?.*["\']?$'
        existing_match = re.search(description_pattern, frontmatter, re.MULTILINE)

        # Escape quotes in description
        escaped_description = description.replace('"', '\\"')

        if existing_match:
            # Replace existing description
            new_frontmatter = re.sub(
                description_pattern,
                f'description: "{escaped_description}"',
                frontmatter,
                count=1,
                flags=re.MULTILINE
            )
        else:
            # Add new description at the end of frontmatter
            new_frontmatter = frontmatter.rstrip() + f'\ndescription: "{escaped_description}"'

        # Reconstruct file
        new_content = f"---\n{new_frontmatter}\n---\n{body}"

        # Write back only if changed
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True

        return False

    except Exception as e:
        raise RuntimeError(f"Failed to update {filepath}: {e}")


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
    config_path: str
) -> None:
    """
    Post inline meta description suggestions as PR review comments.

    Args:
        meta_descriptions: Dictionary mapping variable names to meta descriptions
        owner: Repository owner
        repo: Repository name
        pr_number: Pull request number
        config_path: Path to configuration file

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

    # Get the PR's head commit SHA
    pr_api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        pr_response = requests.get(pr_api_url, headers=headers)
        pr_response.raise_for_status()
        pr_data = pr_response.json()
        commit_sha = pr_data['head']['sha']
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to get PR data: {e}")

    # Build review comments by iterating through all markdown files
    comments = []
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

        # Get relative path for GitHub API
        relative_path = os.path.relpath(filepath, directory)
        description = meta_descriptions[variable_name]
        escaped_description = description.replace('"', '\\"')

        # Create suggestion comment
        comment = {
            "path": relative_path,
            "body": f'```suggestion\ndescription: "{escaped_description}"\n```',
            "line": 2  # Suggest at line 2 (after opening ---)
        }
        comments.append(comment)

    if not comments:
        print("No valid file paths found for suggestions")
        return

    # Post review with comments
    review_api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
    review_body = {
        "commit_id": commit_sha,
        "body": "🤖 Meta description suggestions generated by docdigest",
        "event": "COMMENT",
        "comments": comments
    }

    try:
        response = requests.post(review_api_url, headers=headers, json=review_body)
        response.raise_for_status()

        review_url = response.json().get('html_url', '')
        print(f"✅ Posted {len(comments)} meta description suggestions to PR #{pr_number}")
        if review_url:
            print(f"   View at: {review_url}")

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to post PR review: {e}")


if __name__ == "__main__":
    # Example usage
    sample_meta = {
        "getting_started": "Learn how to quickly set up and configure our platform with step-by-step instructions and comprehensive guides.",
        "api_reference": "Explore our complete API reference with detailed endpoint documentation, authentication methods, and code examples."
    }

    # Update local files
    update_markdown_meta(sample_meta, "docdigest_config.json")
