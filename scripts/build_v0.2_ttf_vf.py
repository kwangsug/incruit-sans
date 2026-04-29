#!/usr/bin/env python3
"""
Incruit Sans v0.2 — TTF + hinted + Variable Font supplements.

Adds three deliverables on top of the v0.2 OTF build:
1. TTF (TrueType) versions of the 4 weights — better Windows compatibility,
   prerequisite for ttfautohint.
2. Hinted TTF versions — ttfautohint applied for crisp 9pt rendering.
3. Variable Font — PretendardVariable.ttf rebranded as IncruitSans-Variable.ttf.

Limitations (documented honestly):
- Variable Font Latin glyphs are Pretendard's (Inter style), NOT Source Sans 3.
  Replacing Latin in a VF requires manipulating master deltas across the entire
  designspace; that is a v0.3 font engineer task.
- Static OTF Latin glyphs (v0.2 main build) lost their original CFF hints during
  glyph transplant via T2CharStringPen. Static TTF + ttfautohint addresses this
  for the TTF deliverable.
"""
import sys
import shutil
import subprocess
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._n_a_m_e import NameRecord
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen

PROJECT_ROOT = Path(__file__).parent.parent
OTF_DIR = PROJECT_ROOT / "build" / "v0.2"
TTF_DIR = PROJECT_ROOT / "build" / "v0.2-ttf"
VF_DIR = PROJECT_ROOT / "build" / "v0.2-vf"
PRETENDARD_VF = PROJECT_ROOT / "src" / "pretendard-1.3.9" / "public" / "variable" / "PretendardVariable.ttf"

WEIGHTS = ["Light", "Regular", "Medium", "Bold"]
TTFAUTOHINT = shutil.which("ttfautohint")

VERSION = "0.2.0"
FAMILY_NAME = "Incruit Sans"
COPYRIGHT = (
    "Copyright (c) 2026 Incruit Corp. "
    "Hangul glyphs based on Pretendard (Copyright 2021 Kil Hyung-jin), licensed under SIL OFL 1.1. "
    "Latin glyphs based on Source Sans 3 (Copyright 2010-2020 Adobe / Paul D. Hunt), licensed under SIL OFL 1.1."
)
COPYRIGHT_VF = (
    "Copyright (c) 2026 Incruit Corp. "
    "Variable Font based on Pretendard Variable (Copyright 2021 Kil Hyung-jin), licensed under SIL OFL 1.1."
)
MANUFACTURER = "Incruit Corp."
LICENSE_DESCRIPTION = (
    "This Font Software is licensed under the SIL Open Font License, Version 1.1."
)
LICENSE_URL = "https://openfontlicense.org"
VENDOR_URL = "https://www.incruit.com"


def set_name(name_table, name_id: int, value: str) -> None:
    name_table.setName(value, name_id, 1, 0, 0)
    name_table.setName(value, name_id, 3, 1, 0x409)


# -----------------------------------------------------------------------------
# CFF → TTF conversion
# -----------------------------------------------------------------------------

def cff_to_ttf(cff_font: TTFont) -> TTFont:
    """Convert CFF outlines to TrueType (quadratic) outlines."""
    glyph_set = cff_font.getGlyphSet()
    glyph_order = cff_font.getGlyphOrder()

    new_glyphs: dict[str, "Glyph"] = {}
    for glyph_name in glyph_order:
        pen = TTGlyphPen(None)
        cu2qu_pen = Cu2QuPen(pen, max_err=1.0, reverse_direction=True)
        glyph_set[glyph_name].draw(cu2qu_pen)
        new_glyphs[glyph_name] = pen.glyph()

    cff_font.setGlyphOrder(glyph_order)

    from fontTools.ttLib.tables._g_l_y_f import table__g_l_y_f
    from fontTools.ttLib.tables._l_o_c_a import table__l_o_c_a
    from fontTools.ttLib.tables._m_a_x_p import table__m_a_x_p

    glyf_table = table__g_l_y_f()
    glyf_table.glyphs = new_glyphs
    glyf_table.glyphOrder = glyph_order
    cff_font["glyf"] = glyf_table
    cff_font["loca"] = table__l_o_c_a()

    new_maxp = table__m_a_x_p()
    new_maxp.tableVersion = 0x00010000
    new_maxp.numGlyphs = len(glyph_order)
    new_maxp.maxPoints = 0
    new_maxp.maxContours = 0
    new_maxp.maxCompositePoints = 0
    new_maxp.maxCompositeContours = 0
    new_maxp.maxZones = 2
    new_maxp.maxTwilightPoints = 0
    new_maxp.maxStorage = 0
    new_maxp.maxFunctionDefs = 0
    new_maxp.maxInstructionDefs = 0
    new_maxp.maxStackElements = 0
    new_maxp.maxSizeOfInstructions = 0
    new_maxp.maxComponentElements = 0
    new_maxp.maxComponentDepth = 0
    cff_font["maxp"] = new_maxp

    if "CFF " in cff_font:
        del cff_font["CFF "]

    cff_font.sfntVersion = "\x00\x01\x00\x00"

    head = cff_font["head"]
    head.indexToLocFormat = 1
    head.glyphDataFormat = 0

    return cff_font


def build_ttf_weights() -> list[Path]:
    print(f"\n[1/3] CFF (OTF) → TTF conversion")
    TTF_DIR.mkdir(parents=True, exist_ok=True)
    out_paths: list[Path] = []
    for weight in WEIGHTS:
        otf_path = OTF_DIR / f"IncruitSans-{weight}.otf"
        if not otf_path.exists():
            raise FileNotFoundError(otf_path)
        font = TTFont(str(otf_path))
        font = cff_to_ttf(font)
        ttf_path = TTF_DIR / f"IncruitSans-{weight}.ttf"
        font.save(str(ttf_path))
        size_mb = ttf_path.stat().st_size / (1024 * 1024)
        print(f"  ✓ {weight:8s} → {ttf_path.name} ({size_mb:.1f}M)")
        out_paths.append(ttf_path)
    return out_paths


# -----------------------------------------------------------------------------
# Hinting via ttfautohint
# -----------------------------------------------------------------------------

def autohint_ttfs(ttf_paths: list[Path]) -> list[Path]:
    print(f"\n[2/3] ttfautohint (hint instructions for 9pt rendering)")
    if not TTFAUTOHINT:
        print("  ⚠️  ttfautohint not found; skipping (install: brew install ttfautohint)")
        return []
    out_paths: list[Path] = []
    for src_path in ttf_paths:
        out_path = src_path.with_name(src_path.stem + "-hinted.ttf")
        result = subprocess.run(
            [
                TTFAUTOHINT,
                "--no-info",
                "--composites",
                "--default-script=latn",
                "--fallback-script=latn",
                "--hinting-range-min=8",
                "--hinting-range-max=72",
                str(src_path),
                str(out_path),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"  ✗ {src_path.stem}: {result.stderr.strip().splitlines()[-1] if result.stderr else 'failed'}")
            continue
        out_paths.append(out_path)
        size_mb = out_path.stat().st_size / (1024 * 1024)
        print(f"  ✓ {src_path.stem:30s} → {out_path.name} ({size_mb:.1f}M)")
    if out_paths:
        for p in out_paths:
            final_name = p.name.replace("-hinted.ttf", ".ttf")
            shutil.move(str(p), str(p.parent / final_name))
            print(f"    renamed → {final_name}")
    return [p.parent / p.name.replace("-hinted.ttf", ".ttf") for p in out_paths]


def generate_woff2_for_ttf() -> None:
    print(f"\n  Generating WOFF2 from hinted TTF…")
    for weight in WEIGHTS:
        ttf_path = TTF_DIR / f"IncruitSans-{weight}.ttf"
        if not ttf_path.exists():
            continue
        font = TTFont(str(ttf_path))
        font.flavor = "woff2"
        woff2_path = TTF_DIR / f"IncruitSans-{weight}.woff2"
        font.save(str(woff2_path))
        size_kb = woff2_path.stat().st_size / 1024
        print(f"    ✓ {weight:8s} → {woff2_path.name} ({size_kb:.0f}K)")


# -----------------------------------------------------------------------------
# Variable Font (rebrand Pretendard VF)
# -----------------------------------------------------------------------------

def build_variable_font() -> Path | None:
    print(f"\n[3/3] Variable Font (rebrand Pretendard VF)")
    if not PRETENDARD_VF.exists():
        print(f"  ✗ Pretendard VF not found: {PRETENDARD_VF}")
        return None

    VF_DIR.mkdir(parents=True, exist_ok=True)
    font = TTFont(str(PRETENDARD_VF))
    nt = font["name"]
    for nid in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 16, 17, 21, 22, 25]:
        nt.removeNames(nameID=nid)

    full = f"{FAMILY_NAME} Variable"
    set_name(nt, 0, COPYRIGHT_VF)
    set_name(nt, 1, FAMILY_NAME)
    set_name(nt, 2, "Regular")
    set_name(nt, 3, f"{MANUFACTURER}: {full}: {VERSION}")
    set_name(nt, 4, full)
    set_name(nt, 5, f"Version {VERSION}")
    set_name(nt, 6, "IncruitSans-Variable")
    set_name(nt, 7, "Incruit Sans is a trademark of Incruit Corp.")
    set_name(nt, 8, MANUFACTURER)
    set_name(nt, 9, "Incruit AX Office (based on Pretendard Variable by Kil Hyung-jin)")
    set_name(nt, 11, VENDOR_URL)
    set_name(nt, 13, LICENSE_DESCRIPTION)
    set_name(nt, 14, LICENSE_URL)
    set_name(nt, 16, FAMILY_NAME)
    set_name(nt, 17, "Variable")

    if "fvar" in font:
        for instance in font["fvar"].instances:
            try:
                axes = instance.coordinates
                weight_val = axes.get("wght", 400)
                if weight_val == 400:
                    instance_name = "Regular"
                elif weight_val == 700:
                    instance_name = "Bold"
                elif weight_val == 300:
                    instance_name = "Light"
                elif weight_val == 500:
                    instance_name = "Medium"
                else:
                    instance_name = f"Weight {int(weight_val)}"
                old_id = instance.subfamilyNameID
                if old_id and old_id >= 256:
                    nt.removeNames(nameID=old_id)
                new_id = nt.addMultilingualName({"en": instance_name})
                instance.subfamilyNameID = new_id
            except Exception:
                pass

    out_ttf = VF_DIR / "IncruitSans-Variable.ttf"
    font.save(str(out_ttf))
    size_mb = out_ttf.stat().st_size / (1024 * 1024)
    print(f"  ✓ {out_ttf.name} ({size_mb:.1f}M)")

    font.flavor = "woff2"
    out_woff2 = VF_DIR / "IncruitSans-Variable.woff2"
    font.save(str(out_woff2))
    size_kb = out_woff2.stat().st_size / 1024
    print(f"  ✓ {out_woff2.name} ({size_kb:.0f}K)")

    return out_ttf


def main() -> int:
    if not OTF_DIR.exists():
        print(f"✗ v0.2 OTF build missing. Run scripts/build_v0.2.py first.", file=sys.stderr)
        return 1

    ttf_paths = build_ttf_weights()
    autohint_ttfs(ttf_paths)
    generate_woff2_for_ttf()
    build_variable_font()

    license_src = PROJECT_ROOT / "src" / "pretendard-1.3.9" / "LICENSE.txt"
    if license_src.exists():
        for d in [TTF_DIR, VF_DIR]:
            shutil.copy(license_src, d / "OFL.txt")

    print(f"\n✓ Done.\n  TTF:           {TTF_DIR}\n  Variable Font: {VF_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
