"""
Git commit management functionality for docdigest.
Handles individual commits for each summary change with interactive and automated modes.
"""

import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional
from .git_utils import (
    run_git_command,
    is_git_repository,
    get_current_branch,
    is_working_directory_clean,
    has_git_config,
    validate_git_state,
    create_branch,
    get_current_commit_hash,
    delete_branch,
    branch_exists
)

# Consistent branch name for all docdigest updates
DOCDIGEST_BRANCH_NAME = "docdigest-auto-updates"


def create_backup(file_path: str) -> Optional[str]:
    """
    Create a backup of the file.

    Args:
        file_path: Path to file to backup

    Returns:
        Backup file path or None if failed
    """
    if not os.path.exists(file_path):
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.backup_{timestamp}"

    try:
        shutil.copy2(file_path, backup_path)
        return backup_path
    except Exception as e:
        print(f"🚨 Failed to create backup: {e}")
        return None


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
        print(f"🚨 Error parsing summaries file: {e}")

    return summaries


def write_summaries_file(file_path: str, summaries: Dict[str, str]) -> bool:
    """
    Write summaries dictionary to the summaries.js file.

    Args:
        file_path: Path to summaries.js file
        summaries: Dictionary of variable names to summary values

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("/*\nSummaries for each topic, matched by filename\n*/\n\n")

            # Write all summaries
            for var_name, value in summaries.items():
                # Escape quotes in the value
                escaped_value = value.replace('"', '\\"')
                f.write(f'const {var_name} = "{escaped_value}";\n')

            f.write("\n\nmodule.exports = {\n")
            f.write(",\n".join(f"  {var_name}" for var_name in summaries.keys()))
            f.write("\n};\n")
        return True
    except Exception as e:
        print(f"🚨 Failed to write file: {e}")
        return False


def get_summaries_changes(old_summaries: Dict[str, str], new_summaries: Dict[str, str]) -> List[Dict]:
    """
    Compare old vs new summaries and return individual changes.

    Args:
        old_summaries: Previous summaries (variable: value)
        new_summaries: Current summaries (variable: value)

    Returns:
        List of change dictionaries with type, variable, and optional line
    """
    changes = []

    # Find added and modified
    for var_name, new_value in new_summaries.items():
        if var_name not in old_summaries:
            changes.append({
                "type": "add",
                "variable": var_name,
                "line": f'const {var_name} = "{new_value}";'
            })
        elif old_summaries[var_name] != new_value:
            changes.append({
                "type": "update",
                "variable": var_name,
                "line": f'const {var_name} = "{new_value}";'
            })

    # Find removed
    for var_name in old_summaries:
        if var_name not in new_summaries:
            changes.append({
                "type": "remove",
                "variable": var_name
            })

    return changes


def commit_individual_change(file_path: str, change: Dict) -> tuple[bool, Optional[str]]:
    """
    Create individual commit for a single change.

    Args:
        file_path: Path to the file being committed
        change: Change dictionary from get_summaries_changes()

    Returns:
        Tuple of (success: bool, commit_hash: Optional[str])
    """
    # Stage the file
    success, _, stderr = run_git_command(['git', 'add', file_path])
    if not success:
        print(f"🚨 Failed to stage file: {stderr}")
        return False, None

    # Create commit message
    change_type = change["type"].capitalize()
    variable = change["variable"]
    commit_message = f"{change_type} summary for {variable}"

    # Commit the change
    success, stdout, stderr = run_git_command(['git', 'commit', '-m', commit_message])
    if not success:
        print(f"🚨 Failed to commit: {stderr}")
        return False, None

    # Get the commit hash
    success, commit_hash, _ = run_git_command(['git', 'rev-parse', 'HEAD'])

    return True, commit_hash if success else None


def rollback_commits(commit_hashes: List[str]) -> bool:
    """
    Rollback a series of commits.

    Args:
        commit_hashes: List of commit hashes to rollback (in order they were created)

    Returns:
        True if rollback successful, False otherwise
    """
    if not commit_hashes:
        return True

    # Reset to before the first commit
    success, _, stderr = run_git_command(['git', 'reset', '--hard', f'{commit_hashes[0]}~1'])
    if not success:
        print(f"🚨 Failed to rollback commits: {stderr}")
        return False

    print(f"✅ Rolled back {len(commit_hashes)} commits")
    return True


def prompt_user(question: str, default: str = "n") -> bool:
    """
    Prompt user for yes/no input in interactive mode.

    Args:
        question: Question to ask user
        default: Default answer ('y' or 'n')

    Returns:
        True for yes, False for no
    """
    valid_yes = ['yes', 'y']
    valid_no = ['no', 'n']

    prompt = f"{question} (yes/no) [{default}]: "

    while True:
        response = input(prompt).strip().lower()

        if not response:
            response = default

        if response in valid_yes:
            return True
        elif response in valid_no:
            return False
        else:
            print("Please answer 'yes' or 'no'")


def commit_changes(output_file: str, config_path: str, is_automation: bool = False, should_push: bool = False) -> bool:
    """
    Main function to commit changes to summaries file and config file.

    Args:
        output_file: Path to summaries.js file
        config_path: Path to config file
        is_automation: True if running in automation mode, False for interactive
        should_push: True to push to remote after committing

    Returns:
        True if all commits successful, False otherwise
    """
    # Validate git state - allow summaries file and config file to have changes
    is_valid, error_msg = validate_git_state(allowed_files=[output_file, config_path])
    if not is_valid:
        print(f"🚨 {error_msg}")
        return False

    # Capture original branch to restore at the end
    original_branch = get_current_branch()
    print(f"📍 Current branch: {original_branch}")

    try:
        # Interactive mode checks
        if not is_automation:
            # Always use consistent branch name
            print(f"Creating branch: {DOCDIGEST_BRANCH_NAME}")

            # If branch exists locally, delete it first
            if branch_exists(DOCDIGEST_BRANCH_NAME):
                print(f"Branch {DOCDIGEST_BRANCH_NAME} already exists locally, recreating...")
                delete_branch(DOCDIGEST_BRANCH_NAME)

            if not create_branch(DOCDIGEST_BRANCH_NAME):
                print("🚨 Failed to create branch. Aborting.")
                return False

            # Offer backup
            backup_question = "Would you like to create a local backup of summaries.js?"
            if prompt_user(backup_question, "n"):
                backup_path = create_backup(output_file)
                if backup_path:
                    print(f"  • Backup created: {backup_path}")
                else:
                    print("🚨 Failed to create backup")
        else:
            # Automation mode - always use consistent branch
            # Only create branch if not already on it
            if original_branch != DOCDIGEST_BRANCH_NAME:
                print(f"Creating branch: {DOCDIGEST_BRANCH_NAME}")

                # If branch exists locally, delete it first
                if branch_exists(DOCDIGEST_BRANCH_NAME):
                    print(f"Branch {DOCDIGEST_BRANCH_NAME} already exists locally, recreating...")
                    delete_branch(DOCDIGEST_BRANCH_NAME)

                if not create_branch(DOCDIGEST_BRANCH_NAME):
                    print("🚨 Failed to create branch. Aborting.")
                    return False

        # Parse old and new summaries
        # First, get the version from git
        success, old_content, _ = run_git_command(['git', 'show', f'HEAD:{output_file}'])
        old_summaries = {}
        if success and old_content:
            # Parse old content from git
            for line in old_content.split('\n'):
                if line.strip().startswith('const '):
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        var_name = parts[0].replace('const', '').strip()
                        value_part = parts[1].strip()
                        if '"' in value_part:
                            # Extract value between quotes, handling escaped quotes
                            try:
                                value = value_part.split('"')[1]
                                old_summaries[var_name] = value
                            except IndexError:
                                continue

        new_summaries = parse_summaries_file(output_file)

        # Get changes
        changes = get_summaries_changes(old_summaries, new_summaries)

        if not changes:
            print("✅ No changes detected in summaries file")
            return True

        # Commit each change individually by updating the file incrementally
        commit_hashes = []
        failed_change = None

        # Start with old summaries and apply changes one at a time
        current_summaries = old_summaries.copy()

        for i, change in enumerate(changes, 1):
            change_type = change["type"].capitalize()
            variable = change["variable"]
            print(f"[{i}/{len(changes)}] {change_type}: {variable}")

            # Apply this single change to current_summaries
            if change["type"] == "add" or change["type"] == "update":
                current_summaries[variable] = new_summaries[variable]
            elif change["type"] == "remove":
                current_summaries.pop(variable, None)

            # Write the updated summaries to file
            if not write_summaries_file(output_file, current_summaries):
                failed_change = change
                break

            # Now commit this single change
            success, commit_hash = commit_individual_change(output_file, change)

            if not success:
                failed_change = change
                break

            if commit_hash:
                commit_hashes.append(commit_hash)

        # Handle failure
        if failed_change:
            print(f"🚨 Failed to commit change for {failed_change['variable']}")

            # In interactive mode, ask about rollback
            should_rollback = True
            if not is_automation:
                should_rollback = prompt_user(f"Rollback {len(commit_hashes)} completed commits?", "y")

            if should_rollback:
                rollback_commits(commit_hashes)

            return False

        # Success - now commit the config file
        print(f"  • Committed {len(commit_hashes)} summaries")

        # Update and commit config file
        from .config import load_config, save_config
        config = load_config(config_path)
        current_commit = get_current_commit_hash()
        config['commit'] = current_commit
        save_config(config_path, config)

        # Commit the config file
        success, _, _ = run_git_command(['git', 'add', config_path])
        if success:
            success, _, stderr = run_git_command(['git', 'commit', '-m', 'Update docdigest config with latest commit hash'])
            if success:
                print("  • Committed config file with updated commit hash")
            else:
                print(f"⚠️  Failed to commit config file: {stderr}")
        else:
            print("⚠️  Failed to stage config file")

        # Push to remote if requested (before switching branches)
        if should_push:
            from .git_utils import push_to_remote
            current_branch = get_current_branch()

            if current_branch:
                success, error_msg = push_to_remote(current_branch, remote="origin", force=True)

                if success:
                    print(f"  • Successfully pushed to origin/{current_branch}")
                    print("👉 Go to GitHub and create a PR from docdigest-auto-updates to main.")
                else:
                    print(f"⚠️  Failed to push to remote: {error_msg}")
                    print("⚠️  Commits are saved locally but not pushed to remote")

        return True

    finally:
        # Always restore original branch
        current_branch = get_current_branch()
        if current_branch != original_branch and original_branch:
            print(f"\n🔙 Returning to original branch: {original_branch}")
            if create_branch(original_branch) if not branch_exists(original_branch) else run_git_command(['git', 'checkout', original_branch])[0]:
                print(f"  • Switched back to {original_branch}")
            else:
                print(f"⚠️  Failed to switch back to {original_branch}")
                print(f"⚠️  You are currently on: {current_branch}")


if __name__ == "__main__":
    # Example usage
    commit_changes("static/js/summaries.js", "docdigest_config.json", is_automation=False)
