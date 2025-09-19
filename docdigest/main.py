# docdigest/main.py
import sys
import argparse
from .config import load_config
from .parse_docs import parse_markdown_files

def main():
    parser = argparse.ArgumentParser(description='Generate AI summaries for documentation')
    parser.add_argument('--config', default='docdigest_config.json',
                       help='Path to config file')

    args = parser.parse_args()

    try:
        # Load config to get output file and other settings
        config = load_config(args.config)

        # Get output file from config
        output_file = config.get('output_file', 'summaries.js')

        # Run the full pipeline
        print("📖 Parsing documentation...")
        parsed_docs = parse_markdown_files(
            directory = config['directory']  # required field, will raise KeyError if missing
            last_commit = config.get('commit')  # optional field, may not exist on first run
            output_file = config.get('output_file', 'summaries.js')  # optional with default
        )
        print(f"Found {len(parsed_docs)} changed files")

        if not parsed_docs:
            print("No changes detected. Exiting.")
            return

        print(f"Output will be written to: {output_file}")

        # TODO: Add summarization step (part 2)
        # TODO: Add JS file generation step (part 3)
        # TODO: Add git commit step (part 4)

        print("Pipeline completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
