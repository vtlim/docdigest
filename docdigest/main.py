# docdigest/main.py
import sys
import argparse
from .config import load_config
from .parse_docs import parse_markdown_files
from .summarize import generate_summaries
from .import_results import update_markdown_imports
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
