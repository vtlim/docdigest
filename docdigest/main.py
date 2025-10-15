# docdigest/main.py
import sys
import argparse
from .config import load_config
from .parse_docs import parse_markdown_files
from .summarize import generate_summaries
from .imports import update_markdown_imports

def main():
    parser = argparse.ArgumentParser(description='Generate AI summaries for documentation')
    parser.add_argument('--config', default='docdigest_config.json',
                       help='Path to config file')
    parser.add_argument('--model', default='debug', choices=['debug', 'claude'],
                       help='Model to use for summarization')
    parser.add_argument('--dry-run', action='store_true',
                       help='Estimate costs without running summarization')

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

        # TODO: Add git commit step (part 4)

        print("\nPipeline completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
