#!/usr/bin/env python3
"""
Incruit Sans v0.7 lighter variants — reduce Latin gvar delta magnitude to thin
the Latin appearance at non-default weights.

Mechanism:
- Default outline (at our wght 400) unchanged → wght 400 baseline same
- Each gvar delta coordinate scaled by LATIN_DELTA_SCALE (< 1.0)
- Result: at wght 700/900, Latin gets less aggressive bold, appearing lighter
  relative to the bolder Hangul

Variants:
- v07-A: delta scale 1.00 (baseline, identical to v0.7)
- v07-B: delta scale 0.90 (10% less Latin variation)
- v07-C: delta scale 0.80 (20% less Latin variation)
- v07-D: delta scale 0.70 (30% less, aggressive thinning)
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
ROBOTO = PROJECT_ROOT / "src" / "roboto" / "roboto-flex-main" / "fonts" / "RobotoFlex[GRAD,XOPQ,XTRA,YOPQ,YTAS,YTDE,YTFI,YTLC,YTUC,opsz,slnt,wdth,wght].ttf"
OUT_DIR = PROJECT_ROOT / "build" / "v0.7-lighter-variants"

LATIN_RANGES = [(0x0020, 0x007E), (0x00A0, 0x00FF)]
ADVANCE_FACTOR = 1.0

VARIANTS = [
    ("A-baseline", 1.00),
    ("B-090", 0.90),
    ("C-080", 0.80),
    ("D-070", 0.70),
]


def is_composite(font, name):
    glyf = font["glyf"]
    if name not in glyf.glyphs:
        return False
    return getattr(glyf[name], "isComposite", lambda: False)()


def scale_coords(coords, factor):
    out = []
    for c in coords:
        if c is None:
            out.append(None)
        else:
            dx, dy = c
            out.append((int(round(dx * factor)), int(round(dy * factor))))
    return out


def replace_with_delta_scale(vf, vf_name, src_vf, src_name, advance_factor, delta_scale):
    src_glyph_set = src_vf.getGlyphSet()
    if src_name not in src_glyph_set or vf_name not in vf["glyf"].glyphs:
        return False
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
        return True

    if src_name in src_gvar.variations:
        new_deltas = []
        for src_delta in src_gvar.variations[src_name]:
            new_deltas.append(
                TupleVariation(
                    dict(src_delta.axes),
                    scale_coords(src_delta.coordinates, delta_scale),
                )
            )
        vf_gvar.variations[vf_name] = new_deltas
    else:
        if vf_name in vf_gvar.variations:
            del vf_gvar.variations[vf_name]
    return True


def activate_tnum(font):
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


def set_name(nt, nid, value):
    nt.setName(value, nid, 1, 0, 0)
    nt.setName(value, nid, 3, 1, 0x409)


def build_variant(label, delta_scale, roboto_full):
    print(f"\n  Building {label}: Latin delta × {delta_scale}")

    vf = TTFont(str(BASE_VF))
    locks = {axis.axisTag: axis.defaultValue for axis in roboto_full["fvar"].axes if axis.axisTag != "wght"}
    roboto_sliced = instantiateVariableFont(roboto_full, locks)

    src_cmap = roboto_sliced["cmap"].getBestCmap()
    vf_cmap = vf["cmap"].getBestCmap()

    count = 0
    for start, end in LATIN_RANGES:
        for cp in range(start, end + 1):
            if cp not in src_cmap or cp not in vf_cmap:
                continue
            if replace_with_delta_scale(vf, vf_cmap[cp], roboto_sliced, src_cmap[cp], ADVANCE_FACTOR, delta_scale):
                count += 1

    activate_tnum(vf)

    nt = vf["name"]
    name = f"Incruit Sans v07-{label}"
    set_name(nt, 1, name)
    set_name(nt, 4, name)
    set_name(nt, 6, f"IncruitSans-v07{label.replace('-', '')}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_ttf = OUT_DIR / f"IncruitSans-{label}.ttf"
    vf.save(str(out_ttf))
    vf.flavor = "woff2"
    out_woff2 = OUT_DIR / f"IncruitSans-{label}.woff2"
    vf.save(str(out_woff2))
    print(f"    ✓ {out_ttf.name}, {out_woff2.name} ({count} glyphs)")


def main():
    if not BASE_VF.exists() or not ROBOTO.exists():
        print("✗ source missing", file=sys.stderr)
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    roboto_full = TTFont(str(ROBOTO))
    print(f"Building v0.7 lighter variants (Latin delta scaling)")
    for label, scale in VARIANTS:
        build_variant(label, scale, roboto_full)
    print(f"\n✓ Done → {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
