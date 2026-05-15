"""
Filters missing_bw_keys.lang to only entries for materials
that actually have items in the NEI CSV dump.
Strategy: for each BW material, check if its English default name
appears in any multi-capital display name in the CSV.
"""

import csv
import re
from pathlib import Path

CSV_PATH = Path(r"D:\UserData\Eldrinn_Elantey\Downloads\itempanel(bart).csv")
MISSING_KEYS = Path("missing_bw_keys.lang")
OUTPUT = Path("missing_bw_keys_filtered.lang")


def count_uppercase_words(name: str) -> int:
    words = name.split()
    return sum(1 for w in words[1:] if w and w[0].isupper() and w[0].isalpha())


def get_csv_display_names() -> set[str]:
    names = set()
    with CSV_PATH.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = row["Display Name"].strip()
            if count_uppercase_words(name) > 0:
                names.add(name)
    return names


def get_materials_from_missing() -> dict[str, str]:
    """Returns {internal_name: english_name} from missing_bw_keys.lang"""
    materials = {}
    for line in MISSING_KEYS.read_text(encoding="utf-8").splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        # key format: gt.oreprefix.<prefix>.<internal>
        parts = key.strip().split(".")
        if len(parts) < 4:
            continue
        internal = parts[3]
        # derive english name: it appears in the value after the prefix words
        # e.g. "Rhodium-Plated Palladium Bolt" -> material is "Rhodium-Plated Palladium"
        # We'll figure this out from WerkstoffLoader instead
        materials[internal] = value.strip()
    return materials


def main():
    print("Loading CSV display names...")
    display_names = get_csv_display_names()

    print("Loading BW material names from WerkstoffLoader...")
    import sys
    sys.path.insert(0, ".")
    from generate_missing_bw_keys import get_bw_materials
    bw_materials = get_bw_materials()  # {internal_lower: english_name}

    # For each material, check if its english name appears in any CSV display name
    materials_in_csv = set()
    for internal, english in bw_materials.items():
        for dname in display_names:
            if english in dname:
                materials_in_csv.add(internal)
                break

    print(f"Materials found in CSV: {len(materials_in_csv)} / {len(bw_materials)}")

    # Filter missing keys
    lines = MISSING_KEYS.read_text(encoding="utf-8").splitlines()
    kept = []
    current_prefix = None
    prefix_buffer = []

    def flush(buf):
        if buf:
            kept.extend(buf)
            kept.append("")

    for line in lines:
        if not line.strip():
            continue
        if "=" not in line:
            continue
        key = line.split("=", 1)[0].strip()
        parts = key.split(".")
        if len(parts) < 4:
            continue
        prefix = ".".join(parts[:3])
        internal = parts[3]

        if internal not in materials_in_csv:
            continue

        if prefix != current_prefix:
            flush(prefix_buffer)
            prefix_buffer = []
            current_prefix = prefix

        prefix_buffer.append(line)

    flush(prefix_buffer)

    OUTPUT.write_text("\n".join(kept) + "\n", encoding="utf-8")
    print(f"Filtered: {sum(1 for l in kept if '=' in l)} keys -> {OUTPUT}")


if __name__ == "__main__":
    main()
