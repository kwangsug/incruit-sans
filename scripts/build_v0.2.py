#!/usr/bin/env python3
"""
Incruit Sans v0.2 — final build.

Strategy:
- Base: Pretendard (Hangul + structure)
- Latin: Source Sans 3 (Adobe) glyphs replacing Pretendard's Inter-style Latin
- Scale: 2.048× (em normalize) × 1.09× (x-height match) = 2.2323×
  Measured: Pretendard Latin vs Source Sans 3 needs +9.11% to match Hangul x-height
- Latin range: U+0020-U+007E (Basic Latin) + U+00A0-U+00FF (Latin-1 Supplement)
- Rebrand → "Incruit Sans"
- tnum lookup promoted to calt (tabular figures by default)
- 4 weights: Light / Regular / Medium / Bold
"""
import sys
import shutil
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform

PROJECT_ROOT = Path(__file__).parent.parent
PRETENDARD_DIR = PROJECT_ROOT / "src" / "pretendard-1.3.9" / "public" / "static"
SOURCE_SANS_DIR = PROJECT_ROOT / "src" / "OTF"
BUILD_DIR = PROJECT_ROOT / "build" / "v0.2"
LICENSE_SRC = PROJECT_ROOT / "src" / "pretendard-1.3.9" / "LICENSE.txt"

X_HEIGHT_BOOST = 1.09

WEIGHT_PAIRS = {
    "Light": ("Pretendard-Light.otf", "SourceSans3-Light.otf"),
    "Regular": ("Pretendard-Regular.otf", "SourceSans3-Regular.otf"),
    "Medium": ("Pretendard-Medium.otf", "SourceSans3-Medium.otf"),
    "Bold": ("Pretendard-Bold.otf", "SourceSans3-Bold.otf"),
}

LATIN_RANGES: list[tuple[int, int]] = [
    (0x0020, 0x007E),
    (0x00A0, 0x00FF),
]

VERSION = "0.2.0"
FAMILY_NAME = "Incruit Sans"
COPYRIGHT = (
    "Copyright (c) 2026 Incruit Corp. "
    "Hangul glyphs based on Pretendard (Copyright 2021 Kil Hyung-jin), licensed under SIL OFL 1.1. "
    "Latin glyphs based on Source Sans 3 (Copyright 2010-2020 Adobe / Paul D. Hunt), licensed under SIL OFL 1.1."
)
MANUFACTURER = "Incruit Corp."
DESIGNER = (
    "Incruit AX Office (Hangul: based on Pretendard by Kil Hyung-jin; "
    "Latin: based on Source Sans 3 by Paul D. Hunt / Adobe Type)"
)
LICENSE_DESCRIPTION = (
    "This Font Software is licensed under the SIL Open Font License, Version 1.1. "
    "This license is available with a FAQ at: https://openfontlicense.org"
)
LICENSE_URL = "https://openfontlicense.org"
VENDOR_URL = "https://www.incruit.com"


def replace_glyph(dst_font: TTFont, dst_glyph_name: str, src_font: TTFont, src_glyph_name: str, scale: float) -> bool:
    src_glyph_set = src_font.getGlyphSet()
    dst_glyph_set = dst_font.getGlyphSet()
    if src_glyph_name not in src_glyph_set or dst_glyph_name not in dst_glyph_set:
        return False

    src_glyph = src_glyph_set[src_glyph_name]
    new_advance = int(round(src_glyph.width * scale))

    dst_cff = dst_font["CFF "].cff
    dst_top_dict = dst_cff[dst_cff.fontNames[0]]
    char_strings = dst_top_dict.CharStrings

    pen = T2CharStringPen(new_advance, dst_glyph_set)
    transform_pen = TransformPen(pen, Transform(scale, 0, 0, scale, 0, 0))
    src_glyph.draw(transform_pen)

    new_charstring = pen.getCharString(private=char_strings[dst_glyph_name].private)
    char_strings[dst_glyph_name] = new_charstring

    dst_font["hmtx"][dst_glyph_name] = (new_advance, dst_font["hmtx"][dst_glyph_name][1])
    return True


def merge_latin(dst_font: TTFont, src_font: TTFont) -> int:
    em_scale = dst_font["head"].unitsPerEm / src_font["head"].unitsPerEm
    final_scale = em_scale * X_HEIGHT_BOOST
    src_cmap = src_font["cmap"].getBestCmap()
    dst_cmap = dst_font["cmap"].getBestCmap()
    replaced = 0
    for start, end in LATIN_RANGES:
        for cp in range(start, end + 1):
            if cp not in src_cmap or cp not in dst_cmap:
                continue
            if replace_glyph(dst_font, dst_cmap[cp], src_font, src_cmap[cp], final_scale):
                replaced += 1
    return replaced


def set_name(name_table, name_id: int, value: str) -> None:
    name_table.setName(value, name_id, 1, 0, 0)
    name_table.setName(value, name_id, 3, 1, 0x409)


def rebrand(font: TTFont, weight_name: str) -> None:
    name_table = font["name"]
    full_family = FAMILY_NAME
    full_name = f"{FAMILY_NAME} {weight_name}"
    postscript_name = f"IncruitSans-{weight_name}"
    is_bold = weight_name == "Bold"
    subfamily = "Bold" if is_bold else "Regular"
    if is_bold or weight_name == "Regular":
        family = full_family
        typo_family = None
        typo_subfamily = None
    else:
        family = f"{full_family} {weight_name}"
        typo_family = full_family
        typo_subfamily = weight_name

    for nid in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 16, 17, 21, 22]:
        name_table.removeNames(nameID=nid)

    set_name(name_table, 0, COPYRIGHT)
    set_name(name_table, 1, family)
    set_name(name_table, 2, subfamily)
    set_name(name_table, 3, f"{MANUFACTURER}: {full_name}: {VERSION}")
    set_name(name_table, 4, full_name)
    set_name(name_table, 5, f"Version {VERSION}")
    set_name(name_table, 6, postscript_name)
    set_name(name_table, 7, "Incruit Sans is a trademark of Incruit Corp.")
    set_name(name_table, 8, MANUFACTURER)
    set_name(name_table, 9, DESIGNER)
    set_name(name_table, 11, VENDOR_URL)
    set_name(name_table, 13, LICENSE_DESCRIPTION)
    set_name(name_table, 14, LICENSE_URL)
    if typo_family:
        set_name(name_table, 16, typo_family)
        set_name(name_table, 17, typo_subfamily)


def activate_tnum_by_default(font: TTFont) -> bool:
    if "GSUB" not in font:
        return False
    gsub = font["GSUB"].table
    feature_list = gsub.FeatureList
    tnum_lookups: list[int] = []
    for feature_record in feature_list.FeatureRecord:
        if feature_record.FeatureTag == "tnum":
            tnum_lookups.extend(feature_record.Feature.LookupListIndex)
    if not tnum_lookups:
        return False
    for feature_record in feature_list.FeatureRecord:
        if feature_record.FeatureTag in ("calt", "ccmp"):
            existing = set(feature_record.Feature.LookupListIndex)
            for idx in tnum_lookups:
                if idx not in existing:
                    feature_record.Feature.LookupListIndex.append(idx)
                    existing.add(idx)
            feature_record.Feature.LookupCount = len(feature_record.Feature.LookupListIndex)
            return True
    return False


def build_weight(weight_name: str, pretendard_filename: str, source_sans_filename: str) -> tuple[Path, Path]:
    pretendard_path = PRETENDARD_DIR / pretendard_filename
    source_sans_path = SOURCE_SANS_DIR / source_sans_filename
    if not pretendard_path.exists():
        raise FileNotFoundError(pretendard_path)
    if not source_sans_path.exists():
        raise FileNotFoundError(source_sans_path)

    font = TTFont(str(pretendard_path))
    src = TTFont(str(source_sans_path))

    replaced = merge_latin(font, src)
    tnum_promoted = activate_tnum_by_default(font)
    rebrand(font, weight_name)

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    otf_path = BUILD_DIR / f"IncruitSans-{weight_name}.otf"
    font.save(str(otf_path))

    font.flavor = "woff2"
    woff2_path = BUILD_DIR / f"IncruitSans-{weight_name}.woff2"
    font.save(str(woff2_path))

    print(f"  ✓ {weight_name:8s} latin={replaced:3d}  tnum={tnum_promoted}  → {otf_path.name}")
    return otf_path, woff2_path


def main() -> int:
    print(f"Building Incruit Sans v{VERSION} (Source Sans 3 Latin merge, x-height match {X_HEIGHT_BOOST}×)")
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    for weight_name, (pretendard_filename, source_sans_filename) in WEIGHT_PAIRS.items():
        build_weight(weight_name, pretendard_filename, source_sans_filename)
    if LICENSE_SRC.exists():
        shutil.copy(LICENSE_SRC, BUILD_DIR / "OFL.txt")
        print(f"  ✓ OFL license → OFL.txt")
    print(f"\nBuild complete → {BUILD_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
