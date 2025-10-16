# docdigest/main.py
import sys
import argparse
from .config import load_config
from .parse_docs import parse_markdown_files
from .summarize import generate_summaries
from .imports import update_markdown_imports
from .commitify import commit_changes

def main():
    parser = argparse.ArgumentParser(description='Generate AI summaries for documentation')
    parser.add_argument('--config', default='docdigest_config.json',
                       help='Path to config file')
    parser.add_argument('--model', default='debug', choices=['debug', 'claude'],
                       help='Model to use for summarization')
    parser.add_argument('--dry-run', action='store_true',
                       help='Estimate costs without running summarization')
    parser.add_argument('--automation', action='store_true',
                       help='Run in automation mode (no interactive prompts)')

    args = parser.parse_args()

    try:
        # Load config to get output file and other settings
        config = load_config(args.config)

        # Get output file from config
        output_file = config.get('output_file', 'summaries.js')

        # Run the full pipeline
        print("\n📖 Parsing documentation...")
        parsed_docs = parse_markdown_files(
            config['directory'],  # required field, will raise KeyError if missing
            config.get('commit'),  # optional field, may not exist on first run
            args.config
        )
        print(f"Found {len(parsed_docs)} changed files")

        if not parsed_docs:
            print("No changes detected. Exiting.")
            return

        # Dry-run mode: estimate costs and exit
        if args.dry_run:
            from .summarize import estimate_costs
            estimate_costs(parsed_docs, args.model)
            return

        print(f"\n🤖 Generating summaries using {args.model} model...")
        summaries = generate_summaries(
            parsed_docs=parsed_docs,
            model=args.model,
            output_file=output_file
        )

        print("\n📝 Adding imports to Markdown files...")
        update_markdown_imports(summaries, args.config)

        # Commit changes if summaries were generated
        if summaries:
            print("\n📦 Committing changes...")
            commit_success = commit_changes(output_file, is_automation=args.automation)

            # Update config with current commit hash after successful commits
            if commit_success:
                from .git_utils import get_current_commit_hash, is_git_repository, run_git_command, get_current_branch, push_to_remote
                if is_git_repository():
                    from .config import save_config
                    current_commit = get_current_commit_hash()
                    config['commit'] = current_commit
                    save_config(args.config, config)
                    print("✅ Config updated with latest commit hash")

                    # Commit the config file
                    success, _, _ = run_git_command(['git', 'add', args.config])
                    if success:
                        success, _, _ = run_git_command(['git', 'commit', '-m', 'Update docdigest config with latest commit hash'])
                        if success:
                            print("✅ Config file committed")

                            # Push to remote after all commits are done
                            current_branch = get_current_branch()
                            should_push = False

                            if args.automation:
                                # Automation mode - always push
                                should_push = True
                            else:
                                # Interactive mode - ask user
                                from .commitify import prompt_user
                                should_push = prompt_user("Push changes to remote?", "y")

                            if should_push and current_branch:
                                print(f"📤 Pushing {current_branch} to origin...")
                                success, error_msg = push_to_remote(current_branch, remote="origin", force=True)

                                if success:
                                    print(f"✅ Successfully pushed to origin/{current_branch}")
                                else:
                                    print(f"⚠️  Failed to push to remote: {error_msg}")
                                    print("⚠️  Commits are saved locally but not pushed to remote")
                        else:
                            print("⚠️  Failed to commit config file")
                    else:
                        print("⚠️  Failed to stage config file")
                else:
                    print("⚠️  Not in a git repository. Config not updated.")
            else:
                print("⚠️  Commit process had issues. Config not updated.")

        print("Pipeline completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
