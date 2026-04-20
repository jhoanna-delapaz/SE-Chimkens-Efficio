import sys
import re


def main():
    commit_msg_filepath = sys.argv[1]

    with open(commit_msg_filepath, "r") as f:
        # Read lines, strip out comments (lines starting with #) to find the actual commit message
        lines = f.readlines()

    actual_message_lines = [line for line in lines if not line.strip().startswith("#")]

    if not actual_message_lines:
        print("Commit message is empty.")
        sys.exit(1)

    subject = actual_message_lines[0].strip()

    # Automatically allow Git-generated ecosystem commits to pass
    if (
        subject.startswith("Merge ")
        or subject.startswith("Revert ")
        or subject.startswith("Squashed ")
        or subject.startswith("Squash ")
    ):
        sys.exit(0)

    pattern = re.compile(
        r"^(ftr|htfx|epc|tsk|dcmnt|upd|chore|refactor):\s\[([A-Z0-9-]+|No-ID)\]\s.+",
        re.IGNORECASE,
    )

    if not pattern.match(subject) or subject == "type: [ID] description":
        error_msg = f"""
Invalid commit message format: "{subject}"

Required format (CONTRIBUTING.md Standards):
type: [Hierarchical-ID] description

Allowed types:
ftr, htfx, epc, tsk, dcmnt, upd, chore, refactor

Valid Examples:
ftr: [FT01] built search bar
chore: [No-ID] clean up files
"""
        print(error_msg, file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
