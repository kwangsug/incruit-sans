#!/usr/bin/env python3
"""
Incruit Sans v0.1 build script.

Strategy:
- Base: Pretendard (OFL 1.1, orioncactus)
- Rebrand to "Incruit Sans"
- Activate `tnum` (tabular figures) by default via GSUB feature reordering
- Output 4 weights: Light / Regular / Medium / Bold

Phase 1.1 (next): Merge Source Sans 3 Latin glyphs (em scale 1000 → 2048)
"""
import os
import sys
import shutil
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._n_a_m_e import NameRecord

PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src" / "pretendard-1.3.9" / "public" / "static"
BUILD_DIR = PROJECT_ROOT / "build" / "v0.1"

WEIGHTS = {
    "Light": "Pretendard-Light.otf",
    "Regular": "Pretendard-Regular.otf",
    "Medium": "Pretendard-Medium.otf",
    "Bold": "Pretendard-Bold.otf",
}

FAMILY_NAME = "Incruit Sans"
VERSION = "0.1.0"
COPYRIGHT = (
    "Copyright (c) 2026 Incruit Corp. "
    "Based on Pretendard (Copyright 2021 Kil Hyung-jin), licensed under the SIL Open Font License 1.1."
)
MANUFACTURER = "Incruit Corp."
DESIGNER = "Incruit AX Office (based on Pretendard by Kil Hyung-jin)"
LICENSE_DESCRIPTION = (
    "This Font Software is licensed under the SIL Open Font License, Version 1.1. "
    "This license is available with a FAQ at: https://openfontlicense.org"
)
LICENSE_URL = "https://openfontlicense.org"
VENDOR_URL = "https://www.incruit.com"


def rebrand(font: TTFont, weight_name: str) -> None:
    """Replace name table records to brand as Incruit Sans."""
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

    name_table.removeNames(nameID=1)
    name_table.removeNames(nameID=2)
    name_table.removeNames(nameID=3)
    name_table.removeNames(nameID=4)
    name_table.removeNames(nameID=5)
    name_table.removeNames(nameID=6)
    name_table.removeNames(nameID=7)
    name_table.removeNames(nameID=8)
    name_table.removeNames(nameID=9)
    name_table.removeNames(nameID=10)
    name_table.removeNames(nameID=11)
    name_table.removeNames(nameID=13)
    name_table.removeNames(nameID=14)
    name_table.removeNames(nameID=16)
    name_table.removeNames(nameID=17)
    name_table.removeNames(nameID=21)
    name_table.removeNames(nameID=22)

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


def set_name(name_table, name_id: int, value: str) -> None:
    """Write a name record across the standard platform/encoding/lang tuples."""
    name_table.setName(value, name_id, 1, 0, 0)
    name_table.setName(value, name_id, 3, 1, 0x409)


def activate_tnum_by_default(font: TTFont) -> bool:
    """Promote the `tnum` GSUB lookups so tabular figures are used without opt-in."""
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


def build_weight(weight_name: str, source_filename: str) -> Path:
    src_path = SRC_DIR / source_filename
    if not src_path.exists():
        raise FileNotFoundError(f"Source font missing: {src_path}")

    font = TTFont(str(src_path))
    rebrand(font, weight_name)
    tnum_promoted = activate_tnum_by_default(font)

    out_path = BUILD_DIR / f"IncruitSans-{weight_name}.otf"
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    font.save(str(out_path))

    print(f"  ✓ {weight_name:8s} → {out_path.name} (tnum default: {tnum_promoted})")
    return out_path


def main() -> int:
    print(f"Building Incruit Sans v{VERSION} from {SRC_DIR}")
    if not SRC_DIR.exists():
        print(f"  ✗ Source dir not found: {SRC_DIR}", file=sys.stderr)
        return 1

    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)

    for weight_name, source_filename in WEIGHTS.items():
        build_weight(weight_name, source_filename)

    license_src = PROJECT_ROOT / "src" / "pretendard-1.3.9" / "LICENSE.txt"
    license_dst = BUILD_DIR / "OFL.txt"
    if license_src.exists():
        shutil.copy(license_src, license_dst)
        print(f"  ✓ OFL license copied → {license_dst.name}")

    print(f"\nBuild complete → {BUILD_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
