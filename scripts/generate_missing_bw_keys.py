"""
Generates missing BartWorks lang keys for ru_RU.lang.
Compares all (oreprefix x material) combinations against existing translations
and outputs missing entries with English values.
"""

import re
from pathlib import Path

WERKSTOFF_LOADER = Path("src/main/java/bartworks/system/material/WerkstoffLoader.java")
EN_LANG = Path("src/main/resources/assets/gregtech/lang/en_US.lang")
RU_LANG = Path(r"C:\Users\Eldrinn_Elantey\GitHub\GTNH-GregTech-ru_RU\assets\bartworks\lang\ru_RU.lang")
OUTPUT = Path("missing_bw_keys.lang")


def get_bw_materials() -> dict[str, str]:
    """Returns {internal_name_lower: default_english_name}"""
    text = WERKSTOFF_LOADER.read_text(encoding="utf-8")
    blocks = re.split(r"(?=public static final Werkstoff \w+ = new Werkstoff\()", text)
    materials = {}
    for block in blocks:
        if not block.strip().startswith("public static final Werkstoff"):
            continue
        m = re.search(r'"([^"]+)"', block)
        if m:
            name = m.group(1)
            internal = name.replace(" ", "").lower()
            materials[internal] = name
    return materials


def get_en_templates() -> dict[str, str]:
    """Returns {prefix_key: format_string_with_%s}"""
    templates = {}
    for line in EN_LANG.read_text(encoding="utf-8").splitlines():
        if "=" in line and line.startswith("gt.oreprefix.") and "%s" in line:
            k, v = line.split("=", 1)
            templates[k.strip()] = v.strip()
    return templates


def get_existing_ru_keys() -> set[str]:
    keys = set()
    for line in RU_LANG.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            keys.add(line.split("=", 1)[0].strip())
    return keys


def get_ru_prefixes() -> list[str]:
    """Prefixes actually used in ru_RU.lang"""
    prefixes = set()
    for line in RU_LANG.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key = line.split("=", 1)[0].strip()
            parts = key.split(".")
            if len(parts) >= 3:
                prefixes.add(".".join(parts[:3]))
    return sorted(prefixes)


def main():
    materials = get_bw_materials()
    en_templates = get_en_templates()
    existing = get_existing_ru_keys()
    prefixes = get_ru_prefixes()

    missing = []
    for prefix in prefixes:
        template = en_templates.get(prefix)
        if template is None:
            continue
        for internal, english_name in sorted(materials.items()):
            key = f"{prefix}.{internal}"
            if key not in existing:
                en_value = template.replace("%s", english_name)
                missing.append((prefix, key, en_value))

    print(f"Missing: {len(missing)} keys across {len(prefixes)} prefixes\n")

    with OUTPUT.open("w", encoding="utf-8") as f:
        current_prefix = None
        for prefix, key, en_value in missing:
            if prefix != current_prefix:
                if current_prefix is not None:
                    f.write("\n")
                current_prefix = prefix
            f.write(f"{key}={en_value}\n")

    print(f"Written to {OUTPUT}")


if __name__ == "__main__":
    main()
