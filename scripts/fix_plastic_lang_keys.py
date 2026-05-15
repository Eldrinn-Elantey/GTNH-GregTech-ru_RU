"""
Fixes oreprefix lang keys for plastic materials.
For plastics, plate-type oreprefix keys use "sheet" instead of "plate"
(e.g. gt.oreprefix.dense_material_plate.polystyrene -> gt.oreprefix.dense_material_sheet.polystyrene).
"""

import re
import sys
from pathlib import Path

PLASTIC_MATERIALS = {
    "plastic", "rubber", "polyethylene", "epoxid", "epoxidfiberreinforced",
    "polydimethylsiloxane", "silicone", "polysiloxane", "polycaprolactam",
    "polytetrafluoroethylene", "polyvinylchloride", "polystyrene",
    "styrenebutadienerubber", "polybenzimidazole", "radoxpoly", "polyphenylenесulfide",
    # also cover the exact spelling from Java
    "polyphenylenесulfide", "polyphenylenesulfide",
}

# Pattern: gt.oreprefix.<something containing "plate">.<plastic_material>=<value>
KEY_PATTERN = re.compile(
    r'^(gt\.oreprefix\.[^.]*plate[^.]*\.)([^=\s]+)(=.*)$'
)


def fix_line(line: str) -> tuple[str, bool]:
    m = KEY_PATTERN.match(line)
    if not m:
        return line, False
    prefix_part, material, rest = m.group(1), m.group(2), m.group(3)
    if material.lower() not in PLASTIC_MATERIALS:
        return line, False
    new_prefix = prefix_part.replace("_plate", "_sheet")
    if new_prefix == prefix_part:
        return line, False
    return new_prefix + material + rest + "\n", True


def fix_file(path: Path, dry_run: bool) -> int:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    changed = 0
    new_lines = []
    for line in lines:
        new_line, was_changed = fix_line(line)
        new_lines.append(new_line.rstrip("\n"))
        if was_changed:
            changed += 1
            print(f"  {path}: {line.rstrip()} -> {new_line.rstrip()}")
    if changed and not dry_run:
        path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    return changed


def main():
    dry_run = "--dry-run" in sys.argv
    if len(sys.argv) > 1 and not sys.argv[-1].startswith("--"):
        lang_files = [Path(sys.argv[-1])]
    else:
        root = Path(__file__).parent / "src/main/resources"
        lang_files = list(root.rglob("*.lang"))

    total = 0
    for f in lang_files:
        total += fix_file(f, dry_run)

    if dry_run:
        print(f"\nDry run: {total} keys would be renamed.")
    else:
        print(f"\nDone: {total} keys renamed.")


if __name__ == "__main__":
    main()
