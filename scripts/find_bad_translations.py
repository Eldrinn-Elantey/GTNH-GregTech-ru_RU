import csv
import re
import sys

ENGLISH_LETTER = re.compile(r'[A-Za-z]')
# Roman numerals and common abbreviations that are OK to have as uppercase
ROMAN = re.compile(r'^[IVXLCDM]+$')


def count_uppercase_words(name: str) -> int:
    """Count words that start with uppercase, excluding the first word."""
    words = name.split()
    if not words:
        return 0
    # Skip first word (it's expected to be capitalized)
    return sum(1 for w in words[1:] if w and w[0].isupper())


def has_english(name: str) -> bool:
    return bool(ENGLISH_LETTER.search(name))


def check_name(name: str) -> list[str]:
    issues = []
    if has_english(name):
        issues.append("english")
    if count_uppercase_words(name) > 0:
        issues.append("multi-capital")
    return issues


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else r"D:\UserData\Eldrinn_Elantey\Downloads\itempanel(bart).csv"

    results = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["Display Name"].strip()
            issues = check_name(name)
            if issues:
                results.append((row["Item ID"], row["Item meta"], name, ", ".join(issues)))

    print(f"Found {len(results)} problematic entries:\n")
    for item_id, meta, name, issues in results:
        print(f"[{item_id}:{meta}] {name!r}  ({issues})")


if __name__ == "__main__":
    main()
