"""
Sorts every assets/*/lang/ru_RU.lang.

Each key goes to the section of its oreprefix (the third part of
gt.oreprefix.<prefix>.<material>), sections follow the order of SECTIONS, and
keys are sorted alphabetically inside a section. Prefixes missing from SECTIONS
end up under "# Unsorted". Headers and blank lines are regenerated.

A file is written only if it keeps exactly the same key=value lines, so the
script never adds, drops or changes a translation. Duplicate keys are kept and
reported.

Usage: python scripts/sort_lang.py
"""

from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent.parent
LANGS = sorted(ROOT.glob("assets/*/lang/ru_RU.lang"))

WIRE_SIZES = ["1x", "2x", "4x", "8x", "12x", "16x"]
PIPE_SIZES = [("Huge", "huge_"), ("Large", "large_"), ("Normal", ""), ("Small", "small_"), ("Tiny", "tiny_")]
CRACKED = [
    ("Lightly Hydro-Cracked", "lightly_hydro-cracked"),
    ("Lightly Steam-Cracked", "lightly_steam-cracked"),
    ("Moderately Hydro-Cracked", "moderately_hydro-cracked"),
    ("Moderately Steam-Cracked", "moderately_steam-cracked"),
    ("Severely Hydro-Cracked", "severely_hydro-cracked"),
    ("Severely Steam-Cracked", "severely_steam-cracked"),
]

# (section path, oreprefix) in output order. The layout follows gregtech/lang/ru_RU.lang.
SECTIONS = (
    [(("Wires", size), f"{size}_material_wire") for size in WIRE_SIZES]
    + [(("Cables", size), f"{size}_material_cable") for size in WIRE_SIZES]
    + [
        (("Blocks",), "block_of_material"),
        (("Centrifuged Ores",), "centrifuged_material_ore"),
        (("Gems",), "material"),
        (("Gems", "Chipped"), "chipped_material"),
        (("Gems", "Exquisite"), "exquisite_material"),
        (("Gems", "Flawed"), "flawed_material"),
        (("Gems", "Flawless"), "flawless_material"),
        (("Ores",), "material_ore"),
        (("Ores", "Small Ores"), "small_material_ore"),
        (("Ores", "Raw Ores"), "raw_material_ore"),
        (("Ores", "Ground"), "crushed_material_crystals"),
        (("Ores", "Crushed"), "crushed_material_ore"),
        (("Ores", "Purified"), "purified_material_ore"),
        (("Ores", "Purified Dusts"), "purified_pile_of_material_dust"),
        (("Ores", "Impure"), "impure_pile_of_material_dust"),
    ]
    + [(("Pipes", "Fluid Pipes", name), f"{size}material_fluid_pipe") for name, size in PIPE_SIZES]
    + [
        (("Pipes", "Fluid Pipes", "4x"), "quadruple_material_fluid_pipe"),
        (("Pipes", "Fluid Pipes", "9x"), "nonuple_material_fluid_pipe"),
    ]
    + [(("Pipes", "Item Pipes", name), f"{size}material_item_pipe") for name, size in PIPE_SIZES]
    + [(("Pipes", "Restrictive Item Pipes", name), f"{size}restrictive_material_item_pipe") for name, size in PIPE_SIZES]
    + [
        (("Materials", "Crystals"), "shard_of_material"),
        (("Materials", "Bolts"), "material_bolt"),
        (("Materials", "Screws"), "material_screw"),
        (("Materials", "Springs"), "material_spring"),
        (("Materials", "Turbine Blades"), "material_turbine_blade"),
        (("Materials", "Quadruple Plates"), "quadruple_material_plate"),
        (("Materials", "Quintuple Plates"), "quintuple_material_plate"),
        (("Materials", "Small Gears"), "small_material_gear"),
        (("Materials", "Small Springs"), "small_material_spring"),
        (("Materials", "Superdense Plates"), "superdense_material_plate"),
        (("Materials", "Triple Sheets"), "triple_material_sheet"),
        (("Materials", "Dense Sheets"), "dense_material_sheet"),
        (("Materials", "Double Sheets"), "double_material_sheet"),
        (("Materials", "Sheets"), "material_sheet"),
        (("Materials", "Quadruple Sheets"), "quadruple_material_sheet"),
        (("Materials", "Quintuple Sheets"), "quintuple_material_sheet"),
        (("Materials", "Superdense Sheets"), "superdense_material_sheet"),
        (("Materials", "Triple Plates"), "triple_material_plate"),
        (("Materials", "Dense Plates"), "dense_material_plate"),
        (("Materials", "Double Plates"), "double_material_plate"),
        (("Materials", "Fine Wires"), "fine_material_wire"),
        (("Materials", "Hot Ingots"), "hot_material_ingot"),
        (("Materials", "Casings"), "material_casing"),
        (("Materials", "Bolted Casings"), "bolted_material_casing"),
        (("Materials", "Rebolted Casings"), "rebolted_material_casing"),
        (("Materials", "Dusts"), "material_dust"),
        (("Materials", "Small Dusts"), "small_pile_of_material_dust"),
        (("Materials", "Tiny Dusts"), "tiny_pile_of_material_dust"),
        (("Materials", "Foils"), "material_foil"),
        (("Materials", "Frame Boxes"), "material_frame_box"),
        (("Materials", "Frame Boxes (TileEntity)"), "material_frame_box_tileentity"),
        (("Materials", "Gears"), "material_gear"),
        (("Fluid", "Moltens"), "molten_material"),
        (("Fluid", "Plasma"), "material_plasma"),
    ]
    + [(("Fluid", "Cracked Fluids", name), f"{kind}_material") for name, kind in CRACKED]
    + [
        (("Cells",), "material_cell"),
        (("Cells", "Molten Cells"), "molten_material_cell"),
        (("Cells", "Plasma Cells"), "material_plasma_cell"),
    ]
    + [(("Cells", "Cracked Cells", name), f"{kind}_material_cell") for name, kind in CRACKED]
    + [
        (("Tools Parts", "Saw Blades"), "material_saw_blade"),
        (("Tools Parts", "Buzzsaw Blades"), "material_buzzsaw_blade"),
        (("Tools Parts", "Chainsaw Tips"), "material_chainsaw_tip"),
        (("Tools Parts", "Drill Tips"), "material_drill_tip"),
        (("Tools Parts", "File Heads"), "material_file_head"),
        (("Tools Parts", "Hammer Heads"), "material_hammer_head"),
        (("Tools Parts", "Ingots"), "material_ingot"),
        (("Tools Parts", "Lens"), "material_lens"),
        (("Tools Parts", "Nanites"), "material_nanites"),
        (("Tools Parts", "Nuggets"), "material_nugget"),
        (("Tools Parts", "Plates"), "material_plate"),
        (("Tools Parts", "Rings"), "material_ring"),
        (("Tools Parts", "Rods"), "material_rod"),
        (("Tools Parts", "Long Rods"), "long_material_rod"),
        (("Tools Parts", "Rotors"), "material_rotor"),
        (("Tools Parts", "Rounds"), "material_round"),
        (("Tools Parts", "Wrench Tips"), "material_wrench_tip"),
        (("Tools Parts", "Sheetmetal"), "material_sheetmetal"),
        (("Tools Parts", "Ice"), "material_ice"),
        (("Tools Parts", "Raw Ice"), "raw_material_ice"),
    ]
)
UNSORTED = ("Unsorted",)

PREFIX_PATH = {prefix: path for path, prefix in SECTIONS}


def key_of(line: str) -> str:
    return line.split("=", 1)[0]


def section_of(key: str) -> tuple[str, ...]:
    parts = key.split(".")
    if key.startswith("gt.oreprefix.") and len(parts) > 3:
        return PREFIX_PATH.get(parts[2], UNSORTED)
    return UNSORTED


def render(entries: list[str]) -> list[str]:
    by_section: dict[tuple[str, ...], list[str]] = {}
    for line in entries:
        by_section.setdefault(section_of(key_of(line)), []).append(line)

    out: list[str] = []
    opened: tuple[str, ...] = ()
    for path in [path for path, _ in SECTIONS] + [UNSORTED]:
        if path not in by_section:
            continue
        # Headers shared with the previous section are already written.
        common = 0
        while common < min(len(opened), len(path)) and opened[common] == path[common]:
            common += 1
        for depth in range(common, len(path)):
            out.append("#" * (depth + 1) + " " + path[depth])
            if depth < len(path) - 1:
                out.append("")
        out += sorted(by_section[path], key=key_of)
        out.append("")
        opened = path
    return out


def main():
    for lang in LANGS:
        lines = lang.read_text(encoding="utf-8-sig").splitlines()
        entries = [line for line in lines if line.strip() and not line.startswith("#")]
        out = render(entries)

        if Counter(entries) != Counter(line for line in out if line and not line.startswith("#")):
            raise SystemExit(f"{lang}: sorted output lost or changed lines, not written")

        with lang.open("w", encoding="utf-8", newline="") as f:
            f.write("\r\n".join(out))

        dups = sorted(key for key, n in Counter(map(key_of, entries)).items() if n > 1)
        print(f"{lang.relative_to(ROOT)}: {len(entries)} keys" + (f", duplicate keys: {', '.join(dups)}" if dups else ""))


if __name__ == "__main__":
    main()
