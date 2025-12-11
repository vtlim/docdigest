"""
Shared git operations for docdigest.
Contains utilities for git commands, status checks, and repository management.
"""

import subprocess
from typing import List, Optional, Tuple


def run_git_command(command: List[str]) -> Tuple[bool, str, str]:
    """
    Run a git command and return success status with output.

    Args:
        command: Git command as list (e.g., ['git', 'status'])

    Returns:
        Tuple of (success: bool, stdout: str, stderr: str)
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stdout.strip() if e.stdout else "", e.stderr.strip() if e.stderr else ""
    except FileNotFoundError:
        return False, "", "Git command not found"


def is_git_repository() -> bool:
    """
    Check if current directory is a git repository.

    Returns:
        True if git repo exists, False otherwise
    """
    success, _, _ = run_git_command(['git', 'rev-parse', '--git-dir'])
    return success


def get_latest_main_hash() -> str:
    """
    Get the most recent git commit hash for the main branch.

    Returns:
        Commit hash as string

    Raises:
        RuntimeError: If unable to get commit hash
    """
    success, stdout, _ = run_git_command(['git', 'rev-parse', 'main'])
    if not success:
        raise RuntimeError("🚨 Failed to get latest main git commit hash")
    return stdout


def get_current_branch() -> Optional[str]:
    """
    Get the current git branch name.

    Returns:
        Branch name or None if unable to determine
    """
    success, stdout, _ = run_git_command(['git', 'branch', '--show-current'])
    return stdout if success else None


def get_git_changed_files(directory: str, since_commit: str) -> List[str]:
    """
    Get list of changed Markdown files from git since specified commit.

    Args:
        directory: Directory to scan for files
        since_commit: Git commit hash to compare against

    Returns:
        List of changed markdown file paths (no exclusions applied)

    Raises:
        RuntimeError: If git command fails
    """
    import os

    success, stdout, _ = run_git_command(['git', 'diff', '--name-only', f'{since_commit}'])

    if not success:
        raise RuntimeError(f"🚨 Failed to get changed files since commit {since_commit}")

    changed_files = stdout.split('\n') if stdout else []

    # Filter for markdown files in the specified directory
    markdown_files = []
    for file_path in changed_files:
        if (file_path.endswith('.md') and
            file_path.startswith(directory) and
            os.path.exists(file_path)):
            markdown_files.append(file_path)

    return markdown_files


def is_working_directory_clean() -> bool:
    """
    Check if git working directory is clean (no uncommitted changes).

    Returns:
        True if clean, False if there are uncommitted changes
    """
    success, stdout, _ = run_git_command(['git', 'status', '--porcelain'])
    return success and stdout == ""


def has_git_config() -> bool:
    """
    Check if git user.name and user.email are configured.

    Returns:
        True if both are configured, False otherwise
    """
    name_success, _, _ = run_git_command(['git', 'config', 'user.name'])
    email_success, _, _ = run_git_command(['git', 'config', 'user.email'])
    return name_success and email_success


def validate_git_state(allowed_files: Optional[List[str]] = None) -> Tuple[bool, str]:
    """
    Validate git state before committing changes.

    Args:
        allowed_files: List of file paths that are allowed to have changes

    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if not is_git_repository():
        return False, "Not a git repository. Please initialize git first."

    if not has_git_config():
        return False, "Git user.name and user.email not configured. Run:\n  git config user.name 'Your Name'\n  git config user.email 'your@email.com'"

    # Check working directory - allow specific files to have changes
    success, stdout, _ = run_git_command(['git', 'status', '--porcelain'])
    if not success:
        return False, "🚨 Failed to check git status"

    if stdout:
        # There are changes - check if they're all in allowed files
        if allowed_files:
            changed_files = [line.strip().split(None, 1)[1] for line in stdout.split('\n') if line.strip()]
            disallowed_changes = [f for f in changed_files if f not in allowed_files]

            if disallowed_changes:
                return False, f"Working directory has uncommitted changes in: {', '.join(disallowed_changes)}. Please commit or stash them first."
        else:
            return False, "Working directory has uncommitted changes. Please commit or stash them first."

    return True, ""


def create_branch(branch_name: str) -> bool:
    """
    Create and checkout a new git branch.

    Args:
        branch_name: Name of the new branch

    Returns:
        True if successful, False otherwise
    """
    success, _, stderr = run_git_command(['git', 'checkout', '-b', branch_name])
    if not success:
        print(f"🚨 Failed to create branch: {stderr}")
    return success


def delete_branch(branch_name: str) -> bool:
    """
    Delete a local git branch.

    Args:
        branch_name: Name of the branch to delete

    Returns:
        True if successful, False otherwise
    """
    success, _, _ = run_git_command(['git', 'branch', '-D', branch_name])
    return success


def branch_exists(branch_name: str) -> bool:
    """
    Check if a local branch exists.

    Args:
        branch_name: Name of the branch to check

    Returns:
        True if branch exists, False otherwise
    """
    success, stdout, _ = run_git_command(['git', 'branch', '--list', branch_name])
    return success and branch_name in stdout


def push_to_remote(branch_name: str, remote: str = "origin", force: bool = False) -> Tuple[bool, str]:
    """
    Push branch to remote repository.

    Args:
        branch_name: Name of the branch to push
        remote: Name of the remote (default: "origin")
        force: Whether to force push

    Returns:
        Tuple of (success: bool, error_message: str)
    """
    # Build push command
    if force:
        cmd = ['git', 'push', '-f', '-u', remote, branch_name]
    else:
        cmd = ['git', 'push', '-u', remote, branch_name]

    success, stdout, stderr = run_git_command(cmd)

    if not success:
        error_msg = stderr if stderr else stdout
        return False, error_msg

    return True, ""


if __name__ == "__main__":
    # Example usage and tests
    print(f"Is git repository: {is_git_repository()}")

    if is_git_repository():
        print(f"Current branch: {get_current_branch()}")
        print(f"Working directory clean: {is_working_directory_clean()}")
        print(f"Git config valid: {has_git_config()}")

        try:
            commit_hash = get_latest_main_hash()
            print(f"Latest main commit: {commit_hash}")
        except RuntimeError as e:
            print(f"Error: {e}")

        is_valid, error_msg = validate_git_state()
        if is_valid:
            print("✅ Git state is valid")
        else:
            print(f"❌ Git state invalid: {error_msg}")
