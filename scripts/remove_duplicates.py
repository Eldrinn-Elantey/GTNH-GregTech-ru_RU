"""
Remove keys from bartworks ru_RU.lang that already exist in gregtech ru_RU.lang.
"""

GT_LANG = "assets/gregtech/lang/ru_RU.lang"
BW_LANG = "assets/bartworks/lang/ru_RU.lang"


def parse_keys(path):
    keys = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if "=" in line and not line.startswith("#"):
                key = line.split("=", 1)[0]
                keys.add(key)
    return keys


bw_keys = parse_keys(BW_LANG)

kept = []
removed = []

with open(GT_LANG, encoding="utf-8") as f:
    for line in f:
        stripped = line.rstrip("\n")
        if "=" in stripped and not stripped.startswith("#"):
            key = stripped.split("=", 1)[0]
            if key in bw_keys:
                removed.append(stripped)
                continue
        kept.append(line)

with open(GT_LANG, "w", encoding="utf-8") as f:
    f.writelines(kept)

print(f"Removed {len(removed)} duplicate(s) from gregtech:")
for r in removed:
    print(f"  {r}")
