#!/usr/bin/env python3
"""
Finalize Incruit Sans v0.5.0 — fix metadata, restore tnum default.

Takes the v0.4 W2-target VF (Latin merged + weight-shifted) and:
1. Renames properly to "Incruit Sans" v0.5.0
2. Restores tnum default activation (promote to calt)
3. Cleans up name table records
4. Outputs WOFF2

Result: build/v0.5-vf/IncruitSans-Variable.{ttf,woff2}
"""
import sys
import shutil
from pathlib import Path
from fontTools.ttLib import TTFont

PROJECT_ROOT = Path(__file__).parent.parent
SOURCE = PROJECT_ROOT / "build" / "v0.4-weight-variants" / "IncruitSans-W2-target.ttf"
OUT_DIR = PROJECT_ROOT / "build" / "v0.5-vf"

VERSION = "0.5.0"
FAMILY = "Incruit Sans"


def set_name(name_table, name_id: int, value: str):
    name_table.setName(value, name_id, 1, 0, 0)
    name_table.setName(value, name_id, 3, 1, 0x409)


def activate_tnum_default(font: TTFont) -> bool:
    if "GSUB" not in font:
        return False
    gsub = font["GSUB"].table
    feature_list = gsub.FeatureList
    tnum_lookups: list[int] = []
    for fr in feature_list.FeatureRecord:
        if fr.FeatureTag == "tnum":
            tnum_lookups.extend(fr.Feature.LookupListIndex)
    if not tnum_lookups:
        return False
    for fr in feature_list.FeatureRecord:
        if fr.FeatureTag == "calt":
            existing = set(fr.Feature.LookupListIndex)
            for idx in tnum_lookups:
                if idx not in existing:
                    fr.Feature.LookupListIndex.append(idx)
                    existing.add(idx)
            fr.Feature.LookupCount = len(fr.Feature.LookupListIndex)
            return True
    return False


def main() -> int:
    if not SOURCE.exists():
        print(f"✗ Source missing: {SOURCE}", file=sys.stderr)
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Finalizing v{VERSION} from {SOURCE.name}")
    f = TTFont(str(SOURCE))

    nt = f["name"]
    for nid in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 16, 17, 21, 22, 25]:
        nt.removeNames(nameID=nid)

    full = f"{FAMILY} Variable"
    copyright_text = (
        "Copyright (c) 2026 Incruit Corp. "
        "Hangul: Pretendard Variable (Copyright 2021 Kil Hyung-jin), OFL 1.1. "
        "Latin: Source Sans 3 VF Upright (Copyright 2010-2020 Adobe / Paul D. Hunt), OFL 1.1."
    )
    designer_text = (
        "Incruit AX Office. "
        "Hangul: Pretendard Variable by Kil Hyung-jin. "
        "Latin: Source Sans 3 VF Upright by Paul D. Hunt / Adobe Type."
    )
    license_desc = "This Font Software is licensed under the SIL Open Font License, Version 1.1."

    set_name(nt, 0, copyright_text)
    set_name(nt, 1, FAMILY)
    set_name(nt, 2, "Regular")
    set_name(nt, 3, f"Incruit Corp.: {full}: {VERSION}")
    set_name(nt, 4, full)
    set_name(nt, 5, f"Version {VERSION}")
    set_name(nt, 6, "IncruitSans-Variable")
    set_name(nt, 7, "Incruit Sans is a trademark of Incruit Corp.")
    set_name(nt, 8, "Incruit Corp.")
    set_name(nt, 9, designer_text)
    set_name(nt, 11, "https://www.incruit.com")
    set_name(nt, 13, license_desc)
    set_name(nt, 14, "https://openfontlicense.org")
    set_name(nt, 16, FAMILY)
    set_name(nt, 17, "Variable")

    tnum_ok = activate_tnum_default(f)
    print(f"  tnum default activation: {'✅' if tnum_ok else '❌'}")

    out_ttf = OUT_DIR / "IncruitSans-Variable.ttf"
    f.save(str(out_ttf))
    print(f"  ✓ {out_ttf.name} ({out_ttf.stat().st_size / (1024*1024):.1f}M)")

    f.flavor = "woff2"
    out_woff2 = OUT_DIR / "IncruitSans-Variable.woff2"
    f.save(str(out_woff2))
    print(f"  ✓ {out_woff2.name} ({out_woff2.stat().st_size / 1024:.0f}K)")

    license_src = PROJECT_ROOT / "src" / "pretendard-1.3.9" / "LICENSE.txt"
    if license_src.exists():
        shutil.copy(license_src, OUT_DIR / "OFL.txt")

    print(f"\n✓ v{VERSION} finalized → {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
