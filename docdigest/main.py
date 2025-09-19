# docdigest/main.py
import sys
import argparse
from .parse_docs import parse_markdown_files

def main():
    parser = argparse.ArgumentParser(description='Generate AI summaries for documentation')
    parser.add_argument('--config', default='docdigest_config.json',
                       help='Path to config file')
    parser.add_argument('--output', default='summaries.js',
                       help='Output JavaScript file')

    args = parser.parse_args()

    try:
        # Run the full pipeline
        print("🔍 Parsing documentation...")
        parsed_docs = parse_markdown_files(args.config)
        print(f"Found {len(parsed_docs)} changed files")

        # TODO: Add summarization, JS generation, git commit steps

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
