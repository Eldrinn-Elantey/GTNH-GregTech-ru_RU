"""
Moves keys from gregtech/lang/ru_RU.lang to addon lang files
based on *_materials.txt files in the repo root.

Output files reproduce the same section structure as the gregtech file,
with keys sorted alphabetically within each section.
"""

import re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent  # repo root (scripts/ is one level deep)
ASSETS = ROOT / "assets"
MATERIALS = ROOT / "materials"
GREGTECH_LANG = ASSETS / "gregtech" / "lang" / "ru_RU.lang"

KEY_RE = re.compile(r"^(gt\.oreprefix\.[^.]+)\.([^=]+)=(.*)$")
GTPP_MAT_RE = re.compile(r"^gtpp\.material\.([^=]+)=")


# ---------------------------------------------------------------------------
# Material list loading
# ---------------------------------------------------------------------------

def load_material_list(txt_file: Path) -> set[str]:
    materials = set()
    lines = txt_file.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "," in line:
            if i == 0 and line == "id,name":
                continue
            parts = line.split(",", 1)
            if len(parts) == 2:
                materials.add(parts[1].strip().strip('"'))
            continue
        m = GTPP_MAT_RE.match(line)
        if m:
            materials.add(m.group(1))
            continue
        materials.add(line)
    return materials


# ---------------------------------------------------------------------------
# Gregtech lang file parsing
# ---------------------------------------------------------------------------

def header_level(line: str) -> int:
    """Return depth of a comment header: # -> 1, ## -> 2, ### -> 3, etc."""
    return len(line) - len(line.lstrip("#"))


class Section:
    def __init__(self, breadcrumb: list[str]):
        # breadcrumb = full hierarchy of headers leading to this section
        # e.g. ["# Wires", "## 1x"]
        self.breadcrumb = list(breadcrumb)
        self.keys: list[str] = []

    def render(self, key_lines: list[str]) -> str:
        sorted_keys = sorted(key_lines, key=lambda l: KEY_RE.match(l).group(2))
        return "\n".join(self.breadcrumb + sorted_keys)


UNSORTED_HEADER = "# Unsorted"


def parse_sections(lang_file: Path) -> tuple[list[Section], Section]:
    """Parse lang file into sections + a separate unsorted section.

    A key is considered "unsorted" when its oreprefix type differs from the
    first key added to the current section (i.e. it was lumped under the wrong
    header because the file isn't fully organised yet).
    """
    sections: list[Section] = []
    unsorted = Section([UNSORTED_HEADER])

    breadcrumb: list[str | None] = []
    current: Section | None = None
    current_prefix: str | None = None  # oreprefix of first key in section

    for line in lang_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            level = header_level(line)
            while len(breadcrumb) < level:
                breadcrumb.append(None)
            breadcrumb[level - 1] = line
            del breadcrumb[level:]
            crumb = [h for h in breadcrumb if h is not None]
            current = Section(crumb)
            current_prefix = None
            sections.append(current)
        elif KEY_RE.match(line):
            m = KEY_RE.match(line)
            prefix = m.group(1)  # e.g. "gt.oreprefix.material_wrench_tip"
            if current is None:
                unsorted.keys.append(line)
            elif current_prefix is None:
                current_prefix = prefix
                current.keys.append(line)
            elif prefix == current_prefix:
                current.keys.append(line)
            else:
                unsorted.keys.append(line)
        # blank lines ignored — regenerated on output

    unsorted.keys.sort(key=lambda l: KEY_RE.match(l).group(0))
    return sections, unsorted


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def render_file(section_key_map: dict[int, list[str]], sections: list[Section]) -> str:
    """Render a lang file from a mapping of section_index -> key lines.

    Only prints breadcrumb headers that changed since the previous section,
    so parent headers like '# Wires' are not duplicated.
    """
    out_lines: list[str] = []
    prev_breadcrumb: list[str] = []

    for idx in sorted(section_key_map):
        keys = section_key_map[idx]
        section = sections[idx]
        # Skip sections that had keys but none survive — their headers aren't useful
        if not keys and section.keys:
            continue

        crumb = section.breadcrumb
        # Find how many leading breadcrumb entries are shared with previous section
        common = 0
        for a, b in zip(prev_breadcrumb, crumb):
            if a == b:
                common += 1
            else:
                break
        new_headers = crumb[common:]

        # Blank line before any new section header
        if out_lines and new_headers:
            out_lines.append("")

        out_lines.extend(new_headers)
        # Unsorted section: sort by full key (prefix first, then material)
        # Normal sections: sort by material name (all keys share the same prefix)
        if crumb and crumb[0] == UNSORTED_HEADER:
            sorted_keys = sorted(keys, key=lambda l: KEY_RE.match(l).group(0))
        else:
            sorted_keys = sorted(keys, key=lambda l: KEY_RE.match(l).group(2))
        out_lines.extend(sorted_keys)

        prev_breadcrumb = crumb

    return "\n".join(out_lines) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Load material lists
    material_to_addon: dict[str, str] = {}
    gregtech_own: set[str] = set()

    for txt in sorted(MATERIALS.glob("*_materials.txt")):
        addon = txt.stem.replace("_materials", "")
        materials = load_material_list(txt)
        if addon == "gregtech":
            gregtech_own = materials
            # Also add stripped versions (no hyphens/underscores) for matching
            gregtech_own |= {re.sub(r'[-_]', '', m) for m in materials}
        else:
            for mat in materials:
                if mat not in material_to_addon:
                    material_to_addon[mat] = addon
                # Also map stripped version -> same addon
                stripped = re.sub(r'[-_]', '', mat)
                if stripped not in material_to_addon:
                    material_to_addon[stripped] = addon
        print(f"Loaded {len(materials):4d} materials for '{addon}'")

    # Parse gregtech lang file
    sections, unsorted = parse_sections(GREGTECH_LANG)
    # Unsorted section gets a virtual index beyond the real sections
    UNSORTED_IDX = len(sections)
    sections.append(unsorted)
    print(f"Parsed {len(sections) - 1} sections + {len(unsorted.keys)} unsorted keys")

    # Distribute keys from normal sections
    gt_keys: dict[int, list[str]] = defaultdict(list)
    addon_keys: dict[str, dict[int, list[str]]] = defaultdict(lambda: defaultdict(list))
    unknown_count = 0

    def route(line: str, idx: int):
        nonlocal unknown_count
        m = KEY_RE.match(line)
        material = m.group(2)
        # Also try stripped version (no hyphens/underscores) for fuzzy matching
        material_stripped = re.sub(r'[-_]', '', material)
        if material in gregtech_own or material_stripped in gregtech_own:
            gt_keys[idx].append(line)
        elif material in material_to_addon:
            addon_keys[material_to_addon[material]][idx].append(line)
        elif material_stripped in material_to_addon:
            addon_keys[material_to_addon[material_stripped]][idx].append(line)
        else:
            gt_keys[idx].append(line)
            unknown_count += 1

    for idx, section in enumerate(sections[:-1]):  # skip unsorted (last)
        for line in section.keys:
            route(line, idx)

    for line in unsorted.keys:
        route(line, UNSORTED_IDX)

    # Keep header-only sections in gregtech
    for idx, section in enumerate(sections):
        if not section.keys and idx not in gt_keys:
            gt_keys[idx] = []

    # Write gregtech file
    GREGTECH_LANG.write_text(render_file(gt_keys, sections), encoding="utf-8")
    kept = sum(len(v) for v in gt_keys.values())
    print(f"\ngregtech: kept {kept} keys", end="")
    if unknown_count:
        print(f"  ({unknown_count} with unknown material)", end="")
    print()

    # Write addon files
    for addon, sec_keys in addon_keys.items():
        lang_file = ASSETS / addon / "lang" / "ru_RU.lang"
        lang_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing keys to avoid duplicates
        existing_keys: set[str] = set()
        existing_content = ""
        if lang_file.exists():
            existing_content = lang_file.read_text(encoding="utf-8")
            for line in existing_content.splitlines():
                em = KEY_RE.match(line)
                if em:
                    existing_keys.add(f"{em.group(1)}.{em.group(2)}")

        # Filter out already-present keys
        filtered: dict[int, list[str]] = {}
        added = 0
        for idx, keys in sec_keys.items():
            new = [l for l in keys
                   if f"{KEY_RE.match(l).group(1)}.{KEY_RE.match(l).group(2)}" not in existing_keys]
            if new:
                filtered[idx] = new
                added += len(new)

        if filtered:
            new_block = render_file(filtered, sections)
            separator = "\n" if existing_content.strip() else ""
            lang_file.write_text(existing_content.rstrip("\n") + separator + new_block, encoding="utf-8")
            print(f"{addon}: added {added} keys")
        else:
            print(f"{addon}: nothing new to add")


if __name__ == "__main__":
    main()
