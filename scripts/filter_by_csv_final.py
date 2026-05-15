"""
Filters missing_bw_keys.lang to only entries for (prefix, material) pairs
that actually appear as untranslated items in the NEI CSV dump.

Strategy:
- Parse WerkstoffLoader: mID -> internal_name
- Parse ru_RU.lang: key -> value (to match display names back to keys)
- For each item_id in CSV, find its oreprefix by matching TRANSLATED display names
  against ru_RU.lang values
- Collect (prefix, internal) pairs that are untranslated (multi-capital) in CSV
- Filter missing_bw_keys.lang to only those pairs
"""

import csv
import re
from collections import defaultdict
from pathlib import Path

CSV_PATH = Path(r"D:\UserData\Eldrinn_Elantey\Downloads\itempanel(bart).csv")
MISSING_KEYS = Path("missing_bw_keys.lang")
RU_LANG = Path(r"C:\Users\Eldrinn_Elantey\GitHub\GTNH-GregTech-ru_RU\assets\bartworks\lang\ru_RU.lang")
OUTPUT = Path("missing_bw_keys_filtered.lang")
WERKSTOFF_LOADER = Path("src/main/java/bartworks/system/material/WerkstoffLoader.java")


def get_mid_to_internal() -> dict[int, str]:
    text = WERKSTOFF_LOADER.read_text(encoding="utf-8")
    blocks = re.split(r"(?=public static final Werkstoff \w+ = new Werkstoff\()", text)
    result = {}
    for block in blocks:
        if not block.strip().startswith("public static final Werkstoff"):
            continue
        m = re.search(r'"([^"]+)"', block)
        if not m:
            continue
        name = m.group(1)
        internal = name.replace(" ", "").lower()
        after = block[m.end():]
        ids = re.findall(r"(?<![{,\[])\s*,\s*(\d{1,5})\s*(?:,|\))", after)
        if ids:
            result[int(ids[0])] = internal
    return result


def count_uppercase_words(name: str) -> int:
    words = name.split()
    return sum(1 for w in words[1:] if w and w[0].isupper() and w[0].isalpha())


def get_ru_value_to_prefix() -> dict[str, str]:
    """Returns {display_value: prefix_key} from ru_RU.lang"""
    result = {}
    for line in RU_LANG.read_text(encoding="utf-8").splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        parts = key.split(".")
        if len(parts) >= 4:
            prefix = ".".join(parts[:3])
            result[value] = prefix
    return result


def main():
    mid_to_internal = get_mid_to_internal()
    internal_to_mid = {v: k for k, v in mid_to_internal.items()}
    print(f"Loaded {len(mid_to_internal)} BW materials with mIDs")

    ru_value_to_prefix = get_ru_value_to_prefix()
    print(f"Loaded {len(ru_value_to_prefix)} ru_RU values for prefix matching")

    # Parse CSV: group by item_id
    # For each item_id: collect (meta, display_name, is_multi_cap)
    item_id_rows: dict[str, list[tuple[int, str, bool]]] = defaultdict(list)
    with CSV_PATH.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            item_id = row["Item ID"]
            try:
                meta = int(row["Item meta"])
            except ValueError:
                continue
            if meta not in mid_to_internal:
                continue
            name = row["Display Name"].strip()
            multi_cap = count_uppercase_words(name) > 0
            item_id_rows[item_id].append((meta, name, multi_cap))

    print(f"Item IDs with BW material metas: {len(item_id_rows)}")

    # For each item_id, determine its prefix by matching translated names
    item_id_to_prefix: dict[str, str] = {}
    for item_id, rows in item_id_rows.items():
        prefix_votes: dict[str, int] = defaultdict(int)
        for meta, name, multi_cap in rows:
            if not multi_cap and name in ru_value_to_prefix:
                prefix_votes[ru_value_to_prefix[name]] += 1
        if prefix_votes:
            item_id_to_prefix[item_id] = max(prefix_votes, key=lambda k: prefix_votes[k])

    # Collect missing (prefix, internal) pairs
    needed: set[tuple[str, str]] = set()
    unmapped_item_ids = set()
    for item_id, rows in item_id_rows.items():
        prefix = item_id_to_prefix.get(item_id)
        if prefix is None:
            unmapped_item_ids.add(item_id)
            continue
        for meta, name, multi_cap in rows:
            if multi_cap:
                internal = mid_to_internal[meta]
                needed.add((prefix, internal))

    print(f"\nItem ID -> Prefix mapping ({len(item_id_to_prefix)} mapped, {len(unmapped_item_ids)} unmapped):")
    for item_id in sorted(item_id_to_prefix):
        prefix = item_id_to_prefix[item_id]
        missing_count = sum(1 for _, _, mc in item_id_rows[item_id] if mc)
        print(f"  {item_id} -> {prefix}  (missing: {missing_count})")
    if unmapped_item_ids:
        print(f"\nUnmapped item IDs (all translations missing, can't determine prefix):")
        for item_id in sorted(unmapped_item_ids):
            rows = item_id_rows[item_id]
            print(f"  {item_id}: {len(rows)} items, e.g. {rows[0][1]!r}")

    print(f"\nTotal (prefix, material) pairs to add: {len(needed)}")

    # Filter missing_bw_keys.lang
    lines = MISSING_KEYS.read_text(encoding="utf-8").splitlines()
    output_lines = []
    current_prefix = None
    prefix_buffer = []

    def flush(buf):
        if buf:
            output_lines.extend(buf)
            output_lines.append("")

    for line in lines:
        if not line.strip() or "=" not in line:
            continue
        key = line.split("=", 1)[0].strip()
        parts = key.split(".")
        if len(parts) < 4:
            continue
        prefix = ".".join(parts[:3])
        internal = parts[3]
        if (prefix, internal) not in needed:
            continue
        if prefix != current_prefix:
            flush(prefix_buffer)
            prefix_buffer = []
            current_prefix = prefix
        prefix_buffer.append(line)

    flush(prefix_buffer)

    OUTPUT.write_text("\n".join(output_lines) + "\n", encoding="utf-8")
    print(f"Written to {OUTPUT}")


if __name__ == "__main__":
    main()
