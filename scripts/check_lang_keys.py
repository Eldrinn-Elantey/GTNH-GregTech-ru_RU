"""
Checks lang keys against GT5-Unofficial sources, where the oreprefix rework
made several key shapes look right while being dead.

Pipes registered with renameMaterial()/displayName() (Wooden, High Pressure,
PBI, PTFE, Plastic, PVC, ...) are looked up by
    gt.oreprefix.<prefix>.material.<material>.<fluidpipe|itempipe>.newname
and NOT by gt.oreprefix.<prefix>.<material>, so the plain key is dead.

GT++ cells generated from a fluid are BaseItemComponent instances whose name
comes from
    OrePrefixes.getLocalizedNameForItem(ComponentTypes.CELL.getName(), "@", materialKey)
with materialKey being Fluid.getUnlocalizedName(), so they are looked up by
    gt.oreprefix.material_cell.fluid.<fluid name>
and NOT by gt.oreprefix.material_cell.<material>. The fluid name is not the item
registry name either: addGTFluidNonMolten prepends "fluid." to it, and dots are
kept in the fluid name but collapsed away in the item name
(froth.copperflotation -> FrothCopperflotation), so both are derived here the
same way the game does.

The cell check needs an item panel dump to tell a dead key from a working one of
the same name, and only reports cells the dump shows in the bracket fallback
form ("[Капсула] Путресцин"). With --apply the dead cell keys are renamed in
place, keeping their translation.

Usage: python scripts/check_lang_keys.py <GT5-Unofficial> [<CropsNH> <itempanel.csv> [--apply]]
"""

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
LANGS = sorted(ROOT.glob("assets/*/lang/*.lang"))
GREGTECH_MATERIALS = ROOT / "materials" / "gregtech_materials.txt"

# --- pipes ------------------------------------------------------------------

LOADER = "src/main/java/gregtech/loaders/preload/LoaderMetaPipeEntities.java"
ID_MAP = "src/main/java/gregtech/api/enums/MaterialsIDMap.java"

KEY_RE = re.compile(r"^(gt\.oreprefix\.([a-z0-9_]*(?:fluid|item)_pipe)\.([^=]+))=")
ID_MAP_RE = re.compile(r"r\((\d+),\s*Materials\.(\w+)\)")
MATERIALS_ARG_RE = re.compile(r"Materials\.(\w+)")
RENAME_RE = re.compile(r"\.(?:renameMaterial|displayName)\(\s*\"")
PIPE_TYPE_RE = re.compile(r"gt\.oreprefix\.[a-z0-9_]*(fluid|item)_pipe")
BUILDER_RE = re.compile(r"(FluidPipeBuilder|ItemPipeBuilder)\.builder\(\)")

# --- cells ------------------------------------------------------------------

CELL_PREFIX_KEY = "gt.oreprefix.material_cell"

# generateFluidNonMolten() registers the fluid as "fluid." + name, the others as is.
FLUID_CALL_RE = re.compile(
    r"(generateFluidNonMolten|generateFluidNoPrefix|generateGas|addGTFluidNonMolten"
    r"|addGTFluidNoPrefix|addGtGas|addGtFluid)\s*\(\s*\"([^\"]+)\""
)
PREFIXED_CALLS = {"generateFluidNonMolten", "addGTFluidNonMolten"}

# CropsNHCellFluid(Reference.MOD_ID + ".fertilizer", new Color(...), "fertilizerCell", ...)
CROPSNH_CALL_RE = re.compile(
    r"new CropsNHCellFluid\(\s*Reference\.MOD_ID\s*\+\s*\"\.(\w+)\"[\s\S]*?\"(\w+)\"",
)

SANITIZED = set(" -_?!@#(){}[]")


def load_lang(path: Path) -> dict[str, str]:
    out = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        key, sep, value = line.partition("=")
        if sep and not key.startswith("#"):
            out[key.strip()] = value
    return out


def load_id_names() -> dict[int, str]:
    """Numeric material id -> internal name, from materials/gregtech_materials.txt."""
    out = {}
    for line in GREGTECH_MATERIALS.read_text(encoding="utf-8").splitlines():
        mid, _, name = line.partition(",")
        if mid.strip().isdigit():
            out[int(mid)] = name.strip().strip('"').lower()
    return out


def load_renamed(gt: Path) -> set[tuple[str, str]]:
    """(material internal name, 'fluidpipe'|'itempipe') for pipes with an overridden name."""
    id_map = {name: int(mid) for mid, name in
              ID_MAP_RE.findall((gt / ID_MAP).read_text(encoding="utf-8"))}
    id_names = load_id_names()
    renamed, material, pipe_type = set(), None, None
    for line in (gt / LOADER).read_text(encoding="utf-8").splitlines():
        if m := BUILDER_RE.search(line):
            pipe_type = "fluidpipe" if m.group(1) == "FluidPipeBuilder" else "itempipe"
            material = None
        elif m := PIPE_TYPE_RE.search(line):
            pipe_type = m.group(1) + "pipe"
        if m := MATERIALS_ARG_RE.search(line):
            material = m.group(1)
        if RENAME_RE.search(line) and material and pipe_type:
            if name := id_names.get(id_map.get(material, -1)):
                renamed.add((name, pipe_type))
    return renamed


def check_pipes(gt: Path) -> list[str]:
    renamed = load_renamed(gt)
    if not renamed:
        return ["no renamed pipes found - GT5U sources changed, update this script"]

    problems = []
    for lang in LANGS:
        for n, line in enumerate(lang.read_text(encoding="utf-8").splitlines(), 1):
            if not (m := KEY_RE.match(line)):
                continue
            key, prefix, rest = m.groups()
            pipe_type = prefix.rsplit("_", 2)[-2] + "pipe"
            parts = rest.split(".")
            if parts[0] == "material":
                if len(parts) != 4 or parts[3] != "newname" or (parts[1], parts[2]) not in renamed:
                    problems.append(f"{lang}:{n}: unexpected override key {key}")
            elif (rest, pipe_type) in renamed:
                problems.append(f"{lang}:{n}: dead key {key} -> "
                                f"gt.oreprefix.{prefix}.material.{rest}.{pipe_type}.newname")
    print(f"pipes: {len(renamed)} renamed pipe material(s) known")
    return problems


def sanitize(text: str) -> str:
    """gregtech.api.util.StringUtils.sanitizeString"""
    return "".join(c for c in text if c not in SANITIZED)


def split_and_uppercase(name: str) -> str:
    """gregtech.api.util.StringUtils.splitAndUppercase"""
    if "." not in name:
        return name
    return "".join(sanitize(part)[:1].upper() + sanitize(part)[1:] for part in name.split("."))


def item_registry_name(fluid_name: str) -> str:
    """The name BaseItemComponent registers the generated cell under."""
    name = fluid_name
    for marker in ("molten.", "fluid."):
        if marker in name:
            name = name.replace(marker, "")
            name = name[:1].upper() + name[1:]
    return split_and_uppercase(name)


def collect_cells(gt: Path, cropsnh: Path) -> dict[str, str]:
    """Item registry name -> fluid internal name."""
    out = {}
    for path in (gt / "src/main/java/gtPlusPlus").rglob("*.java"):
        text = path.read_text(encoding="utf-8", errors="replace")
        for call, name in FLUID_CALL_RE.findall(text):
            fluid_name = ("fluid." + name) if call in PREFIXED_CALLS else name
            out[item_registry_name(fluid_name)] = sanitize(fluid_name.lower())
    for path in (cropsnh / "src/main/java").rglob("*.java"):
        text = path.read_text(encoding="utf-8", errors="replace")
        for fluid, cell_item in CROPSNH_CALL_RE.findall(text):
            out[cell_item] = ("cropsnh." + fluid).lower()
    return out


def collect_bracketed_items(dump: Path) -> set[str]:
    """Item registry names the dump shows in the oreprefix fallback form."""
    with dump.open(encoding="utf-8", newline="") as f:
        return {
            row["Item Name"].split(":", 1)[1]
            for row in csv.DictReader(f)
            if row["Display Name"].startswith("[")
        }


def check_cells(gt: Path, cropsnh: Path, dump: Path, apply: bool) -> list[str]:
    bracketed = collect_bracketed_items(dump)
    cells = {k: v for k, v in collect_cells(gt, cropsnh).items() if k in bracketed}
    print(f"cells: {len(cells)} broken fluid-backed cell(s) in the dump")
    for name in sorted(bracketed - set(cells)):
        print(f"  not a fluid-backed cell, skipped: {name}")

    known = set()
    for path in LANGS:
        known.update(load_lang(path))

    renames, problems = {}, []
    for item_name, fluid_name in sorted(cells.items()):
        new_key = f"{CELL_PREFIX_KEY}.fluid.{fluid_name}"
        if new_key in known:
            continue
        old_key = f"{CELL_PREFIX_KEY}.{item_name.lower()}"
        if old_key in known:
            renames[old_key] = new_key
        else:
            problems.append(f"{item_name}: no translation for {new_key}")

    for path in LANGS:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        changed = 0
        for i, line in enumerate(lines):
            key, sep, value = line.partition("=")
            if sep and key.strip() in renames:
                new_key = renames[key.strip()]
                if apply:
                    lines[i] = f"{new_key}={value}"
                else:
                    problems.append(f"{path}:{i + 1}: dead key {key.strip()} -> {new_key}")
                changed += 1
        if changed and apply:
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(f"{path}: {changed} key(s) renamed")
    return problems


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    gt = Path(sys.argv[1])
    apply = "--apply" in sys.argv
    rest = [a for a in sys.argv[2:] if not a.startswith("--")]

    problems = check_pipes(gt)
    if len(rest) == 2:
        problems += check_cells(gt, Path(rest[0]), Path(rest[1]), apply)
    else:
        print("cells: skipped, pass a CropsNH checkout and an itempanel.csv dump")

    for p in problems:
        print(p)
    print(f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
