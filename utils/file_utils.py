def read_file_lines(file_path: str) -> list[str]:
    try:
        # Read text files in a forgiving way. Log files are often messy, so
        # decoding errors are ignored instead of aborting the whole import.
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.readlines()
    except Exception as e:
        # Return an empty list instead of bubbling the exception up.
        # The parsers can then stay simple and treat unreadable files as empty input.
        print(f"Error reading {file_path}: {e}")
        return []
