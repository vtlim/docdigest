# docdigest/main.py
import sys
import argparse
from .config import load_config
from .parse_docs import parse_markdown_files
from .summarize import generate_summaries, estimate_costs
from .import_results import update_markdown_imports
from .commitify import commit_changes
from .meta_description import generate_meta_descriptions, estimate_costs as estimate_meta_costs
from .import_meta import update_markdown_meta, post_pr_suggestions, get_pr_number, get_repo_info

def main():
    parser = argparse.ArgumentParser(description='Generate AI summaries for documentation')
    parser.add_argument('--config', default='docdigest_config.json',
                       help='Path to config file')
    parser.add_argument('--model', default='debug', choices=['debug', 'claude'],
                       help='Model to use for summarization')
    parser.add_argument('--meta', action='store_true',
                       help='Generate meta descriptions instead of summaries')
    parser.add_argument('--dry-run', action='store_true',
                       help='Estimate costs without running summarization or meta generation')
    parser.add_argument('--automation', action='store_true',
                       help='Run in automation mode (no interactive prompts, auto-commit and push)')

    args = parser.parse_args()

    try:
        # Load config to get output file and other settings
        config = load_config(args.config)

        # Get output file from config
        output_file = config.get('output_file', 'summaries.js')

        # META DESCRIPTION MODE
        if args.meta:
            parsed_docs = None
            pr_changed_files_set = None  # For filtering in automation mode

            # In automation mode, only process PR-changed markdown files
            if args.automation:
                print("\n🔍 Getting PR changed files...")
                try:
                    from .import_meta import get_pr_number, get_repo_info, get_pr_changed_files

                    pr_number = get_pr_number()
                    if not pr_number:
                        raise RuntimeError("Could not determine PR number from environment")

                    owner, repo = get_repo_info()
                    pr_changed_files = get_pr_changed_files(owner, repo, pr_number)

                    # Filter to only markdown files and store in set for fast lookup
                    pr_changed_files_set = {f for f in pr_changed_files if f.endswith('.md')}
                    print(f"  • PR #{pr_number} has {len(pr_changed_files_set)} changed markdown files")

                    if not pr_changed_files_set:
                        print("No markdown files changed in this PR")
                        return

                except Exception as e:
                    print(f"⚠️  Failed to get PR changed files: {e}")
                    return

            # Parse documentation
            print("\n📖 Parsing documentation...")
            parsed_docs = parse_markdown_files(
                config['directory'],
                None if args.automation else config.get('commit'),  # Ignore commit in automation mode
                args.config
            )

            if not parsed_docs:
                print("No files to generate meta descriptions for")
                return

            # Dry-run mode: estimate costs and exit
            if args.dry_run:
                estimate_meta_costs(parsed_docs)
                return

            print(f"\n🤖 Generating meta descriptions using Claude...")
            meta_descriptions = generate_meta_descriptions(
                parsed_docs=parsed_docs,
                output_file=output_file,
                config_path=args.config
            )

            if not meta_descriptions:
                print("🚨 No meta descriptions generated")
                return

            # Automation mode - post PR suggestions
            if args.automation:
                print("\n💬 Posting suggestions to GitHub PR...")
                try:
                    pr_number = get_pr_number()
                    if not pr_number:
                        raise RuntimeError("Could not determine PR number from environment")

                    owner, repo = get_repo_info()

                    post_pr_suggestions(
                        meta_descriptions=meta_descriptions,
                        owner=owner,
                        repo=repo,
                        pr_number=pr_number,
                        config_path=args.config,
                        pr_changed_files=pr_changed_files_set
                    )
                except Exception as e:
                    print(f"⚠️  Failed to post PR suggestions: {e}")
                    return

            # Local mode - update files directly
            else:
                print("\n📝 Updating markdown files...")
                update_markdown_meta(meta_descriptions, args.config)

            print("\n✅ Meta description generation completed!")
            return

        # SUMMARY MODE (existing logic)
        # Run the full pipeline
        print("\n📖 Parsing documentation...")
        parsed_docs = parse_markdown_files(
            config['directory'],  # required field, will raise KeyError if missing
            config.get('commit'),  # optional field, may not exist on first run
            args.config
        )

        # Even if no new summaries needed, we may need to update imports if exclusions changed
        # So don't exit early - continue to update_markdown_imports

        # Dry-run mode: estimate costs and exit
        if args.dry_run:
            if parsed_docs:
                estimate_costs(parsed_docs, args.model)
            else:
                print("No files to estimate costs for")
            return

        # Generate summaries only if there are files to process
        if parsed_docs:
            print(f"\n🤖 Generating summaries using {args.model} model...")
            summaries, changes_to_commit = generate_summaries(
                parsed_docs=parsed_docs,
                model=args.model,
                output_file=output_file,
                config_path=args.config
            )
        else:
            # No new summaries to generate, but filter existing ones for exclusions
            print(f"\n🧹 No new summaries to generate, cleaning up any excluded summaries...")
            summaries, changes_to_commit = generate_summaries(
                parsed_docs={},
                model=args.model,
                output_file=output_file,
                config_path=args.config
            )

        print(f"Summaries are in {output_file}")

        # Update markdown imports (to add new ones or remove old ones)
        if changes_to_commit:
            print("\n📝 Updating markdown file imports...")
            update_markdown_imports(summaries, args.config)

            # In interactive mode, ask if user wants to commit and push
            should_commit = True
            should_push = False

            if not args.automation:
                from .commitify import prompt_user
                should_commit = prompt_user("Commit changes?", "y")

                if should_commit:
                    should_push = prompt_user("Push changes to remote?", "y")
            else:
                # Automation mode - always commit and push
                should_push = True

            if not should_commit:
                print("  • Skipping commit stage")
            else:
                print("\n📦 Committing changes...")
                commit_success = commit_changes(output_file, args.config, is_automation=args.automation, should_push=should_push)

                if not commit_success:
                    print("⚠️  Commit process had issues.")

        print("\n✅ Pipeline completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
