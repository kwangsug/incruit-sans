#!/usr/bin/env python3
"""
Incruit Sans v0.6 — Pretendard + Open Sans VF combination.

Why Open Sans (vs Source Sans 3):
- em == 2048 (same as Pretendard) → NO scaling needed, hinting preserved
- Stroke thickness matches Pretendard within 3% across weight range
- x-height matches within 1% (no boost needed)
- Avoids the +60% stroke mismatch SS3 had at wght 400
- Same OFL 1.1 license

Trade-offs:
- Open Sans wght axis: 300-800 (vs Pretendard 45-930)
  → Latin clamps at extremes (Thin Hangul + Light Latin / Black Hangul + ExtraBold Latin)
- Open Sans advance widths slightly wider (3-6%) → optional density adjustment
- Same composite limitation as v0.5 (i, j, accented chars decomposed to static)

Build steps:
1. Pass A: transplant simple Latin glyphs from Open Sans VF (no scaling, with gvar deltas)
2. Composites decomposed to static (proper handling deferred to v1.0 font engineer work)
3. Restore tnum default
4. Rebrand as Incruit Sans v0.6.0
"""
import sys
import shutil
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.varLib.instancer import instantiateVariableFont

PROJECT_ROOT = Path(__file__).parent.parent
BASE_VF = PROJECT_ROOT / "build" / "v0.2-vf" / "IncruitSans-Variable.ttf"
OPEN_SANS_VF = PROJECT_ROOT / "src" / "opensans" / "opensans-main" / "fonts" / "variable" / "OpenSans[wdth,wght].ttf"
OUT_DIR = PROJECT_ROOT / "build" / "v0.6-vf"

LATIN_RANGES = [(0x0020, 0x007E), (0x00A0, 0x00FF)]
ADVANCE_FACTOR = 0.96  # 4% tighter advance to match Hangul density

VERSION = "0.6.0"
FAMILY = "Incruit Sans"


def is_composite(font, name):
    glyf = font["glyf"]
    if name not in glyf.glyphs:
        return False
    return getattr(glyf[name], "isComposite", lambda: False)()


def replace_simple_glyph(vf, vf_name, src_vf, src_name, advance_factor):
    """Transplant a simple Latin glyph + gvar deltas with no em scaling (em sizes match)."""
    src_glyph_set = src_vf.getGlyphSet()
    if src_name not in src_glyph_set or vf_name not in vf["glyf"].glyphs:
        return False, "missing"

    src_glyph = src_glyph_set[src_name]
    composite = is_composite(src_vf, src_name)
    new_advance = int(round(src_glyph.width * advance_factor))

    pen = TTGlyphPen(None)
    if composite:
        rec = DecomposingRecordingPen(src_glyph_set)
        src_glyph.draw(rec)
        rec.replay(pen)
    else:
        src_glyph.draw(pen)

    vf["glyf"].glyphs[vf_name] = pen.glyph()

    src_lsb = src_vf["hmtx"][src_name][1] if src_name in src_vf["hmtx"].metrics else 0
    new_lsb = int(round(src_lsb * advance_factor))
    vf["hmtx"][vf_name] = (new_advance, new_lsb)

    src_gvar = src_vf["gvar"]
    vf_gvar = vf["gvar"]

    if composite:
        if vf_name in vf_gvar.variations:
            del vf_gvar.variations[vf_name]
        return True, "composite-static"

    if src_name in src_gvar.variations:
        new_deltas = []
        for src_delta in src_gvar.variations[src_name]:
            new_deltas.append(
                TupleVariation(dict(src_delta.axes), list(src_delta.coordinates))
            )
        vf_gvar.variations[vf_name] = new_deltas
        return True, "variable"
    else:
        if vf_name in vf_gvar.variations:
            del vf_gvar.variations[vf_name]
        return True, "no-deltas"


def activate_tnum_default(font):
    if "GSUB" not in font:
        return False
    gsub = font["GSUB"].table
    tnum_lookups = []
    for fr in gsub.FeatureList.FeatureRecord:
        if fr.FeatureTag == "tnum":
            tnum_lookups.extend(fr.Feature.LookupListIndex)
    if not tnum_lookups:
        return False
    for fr in gsub.FeatureList.FeatureRecord:
        if fr.FeatureTag == "calt":
            existing = set(fr.Feature.LookupListIndex)
            for idx in tnum_lookups:
                if idx not in existing:
                    fr.Feature.LookupListIndex.append(idx)
                    existing.add(idx)
            fr.Feature.LookupCount = len(fr.Feature.LookupListIndex)
            return True
    return False


def set_name(name_table, name_id, value):
    name_table.setName(value, name_id, 1, 0, 0)
    name_table.setName(value, name_id, 3, 1, 0x409)


def rebrand(font):
    nt = font["name"]
    for nid in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 16, 17, 21, 22, 25]:
        nt.removeNames(nameID=nid)

    full = f"{FAMILY} Variable"
    copyright_text = (
        "Copyright (c) 2026 Incruit Corp. "
        "Hangul: Pretendard Variable (Copyright 2021 Kil Hyung-jin), OFL 1.1. "
        "Latin: Open Sans (Copyright 2010 Google / Steve Matteson), OFL 1.1."
    )
    designer_text = (
        "Incruit AX Office. "
        "Hangul: Pretendard Variable by Kil Hyung-jin. "
        "Latin: Open Sans by Steve Matteson / Google."
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


def main() -> int:
    if not BASE_VF.exists():
        print(f"✗ Base VF missing: {BASE_VF}", file=sys.stderr)
        return 1
    if not OPEN_SANS_VF.exists():
        print(f"✗ Open Sans VF missing: {OPEN_SANS_VF}", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"v{VERSION} build — Pretendard + Open Sans (em=2048, no scaling)")
    print(f"  advance factor: {ADVANCE_FACTOR}× (4% tighter for Hangul density match)")

    vf = TTFont(str(BASE_VF))

    print(f"\n  Slicing Open Sans VF: lock wdth=100, keep wght variable")
    open_full = TTFont(str(OPEN_SANS_VF))
    open_sliced = instantiateVariableFont(open_full, {"wdth": 100})

    src_cmap = open_sliced["cmap"].getBestCmap()
    vf_cmap = vf["cmap"].getBestCmap()

    counts = {"variable": 0, "composite-static": 0, "no-deltas": 0, "missing": 0}
    print(f"\n  Transplanting Latin glyphs (Basic Latin + Latin-1 Supplement)")
    for start, end in LATIN_RANGES:
        for cp in range(start, end + 1):
            if cp not in src_cmap or cp not in vf_cmap:
                continue
            ok, status = replace_simple_glyph(
                vf, vf_cmap[cp], open_sliced, src_cmap[cp], ADVANCE_FACTOR
            )
            if ok:
                counts[status] = counts.get(status, 0) + 1

    total = sum(counts.values())
    print(f"  ✓ {total} Latin glyphs transplanted:")
    print(f"    - variable (slider works):  {counts['variable']}")
    print(f"    - composite static (i,j,À): {counts['composite-static']}")
    print(f"    - no-deltas (simple fixed): {counts['no-deltas']}")

    tnum_ok = activate_tnum_default(vf)
    print(f"\n  tnum default activation: {'✅' if tnum_ok else '❌'}")

    rebrand(vf)
    print(f"  rebranded as Incruit Sans v{VERSION}")

    out_ttf = OUT_DIR / "IncruitSans-Variable.ttf"
    vf.save(str(out_ttf))
    print(f"\n  ✓ {out_ttf.name} ({out_ttf.stat().st_size / (1024*1024):.1f}M)")

    vf.flavor = "woff2"
    out_woff2 = OUT_DIR / "IncruitSans-Variable.woff2"
    vf.save(str(out_woff2))
    print(f"  ✓ {out_woff2.name} ({out_woff2.stat().st_size / 1024:.0f}K)")

    license_src = PROJECT_ROOT / "src" / "pretendard-1.3.9" / "LICENSE.txt"
    if license_src.exists():
        shutil.copy(license_src, OUT_DIR / "OFL.txt")

    print(f"\n✓ v{VERSION} build complete → {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
