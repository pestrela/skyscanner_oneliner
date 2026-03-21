import sys

from oneliner.skyscanner_parser import parse_text as parse  # re-exported for test_integration.py

if __name__ == "__main__":
    print("Paste flight page text, then press Ctrl+D (Linux):", file=sys.stderr)
    text = sys.stdin.read()

    print("")
    print("*"*10)
    try:
        for leg in parse(text):
            print(leg)
        print("*"*10)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
