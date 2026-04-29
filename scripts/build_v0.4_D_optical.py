#!/usr/bin/env python3
"""
Incruit Sans v0.4 — Option D: Optical per-glyph Latin respacing.

Difference from A/B/C/D-uniform variants:
- A/B/C/D: scale advance width by uniform factor (e.g., × 0.94)
- D-OPTICAL: measure each glyph's ink bounds, reduce LSB/RSB proportionally

Why this is "more designed":
- Narrow glyphs (i, l, j) → side bearings tightened more
- Wide glyphs (M, W, @) → side bearings preserve their visual breathing room
- Result resembles what a font engineer would do manually

Algorithm per Latin glyph:
1. Read source LSB, advance, and measured ink width from BoundsPen
2. Compute source RSB = advance - LSB - ink_width
3. Scale all by outline_scale (2.2323×) → "scaled" reference values
4. Apply SIDE_BEARING_FACTOR (0.70 default) to scaled LSB and RSB
5. Translate glyph so its xMin sits at new_LSB position
6. Set new advance = new_LSB + scaled_ink_width + new_RSB

Side bearing factor 0.70 = 30% reduction in side bearings (not advance).
Empty glyphs (space, NBSP) get advance × scale × factor (no ink to measure).
"""
import sys
import shutil
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.misc.transform import Transform

PROJECT_ROOT = Path(__file__).parent.parent
BASE_VF = PROJECT_ROOT / "build" / "v0.2-vf" / "IncruitSans-Variable.ttf"
SOURCE_VF = PROJECT_ROOT / "src" / "source-sans-vf" / "VF" / "SourceSans3VF-Upright.ttf"
OUT_DIR = PROJECT_ROOT / "build" / "v0.4-advance-variants"

OUTLINE_SCALE = 2.048 * 1.09
SIDE_BEARING_FACTOR = 0.70
LATIN_RANGES = [(0x0020, 0x007E), (0x00A0, 0x00FF)]


def is_composite(font, name):
    glyf = font["glyf"]
    if name not in glyf.glyphs:
        return False
    return getattr(glyf[name], "isComposite", lambda: False)()


def scale_delta_coords(coords, scale):
    out = []
    for c in coords:
        if c is None:
            out.append(None)
        else:
            dx, dy = c
            out.append((int(round(dx * scale)), int(round(dy * scale))))
    return out


def replace_optical(vf, vf_name, src_vf, src_name, outline_scale, sb_factor):
    src_glyph_set = src_vf.getGlyphSet()
    if src_name not in src_glyph_set or vf_name not in vf["glyf"].glyphs:
        return False, "missing"

    src_glyph = src_glyph_set[src_name]
    src_advance = src_glyph.width
    src_lsb = src_vf["hmtx"][src_name][1]

    bounds_pen = BoundsPen(src_glyph_set)
    src_glyph.draw(bounds_pen)
    if bounds_pen.bounds is None:
        new_advance = int(round(src_advance * outline_scale * sb_factor))
        composite = is_composite(src_vf, src_name)
        pen = TTGlyphPen(None)
        tp = TransformPen(pen, Transform(outline_scale, 0, 0, outline_scale, 0, 0))
        if composite:
            rec = DecomposingRecordingPen(src_glyph_set)
            src_glyph.draw(rec)
            rec.replay(tp)
        else:
            src_glyph.draw(tp)
        vf["glyf"].glyphs[vf_name] = pen.glyph()
        vf["hmtx"][vf_name] = (new_advance, 0)
        if "gvar" in vf and vf_name in vf["gvar"].variations:
            del vf["gvar"].variations[vf_name]
        return True, "empty"

    src_xmin, _, src_xmax, _ = bounds_pen.bounds
    src_ink_w = src_xmax - src_xmin
    src_rsb = src_advance - src_lsb - src_ink_w

    scaled_lsb = src_lsb * outline_scale
    scaled_rsb = src_rsb * outline_scale
    scaled_ink_w = src_ink_w * outline_scale
    scaled_xmin = src_xmin * outline_scale

    new_lsb = scaled_lsb * sb_factor
    new_rsb = scaled_rsb * sb_factor
    shift_x = new_lsb - scaled_xmin
    new_advance = int(round(new_lsb + scaled_ink_w + new_rsb))

    composite = is_composite(src_vf, src_name)

    pen = TTGlyphPen(None)
    tp = TransformPen(pen, Transform(outline_scale, 0, 0, outline_scale, shift_x, 0))
    if composite:
        rec = DecomposingRecordingPen(src_glyph_set)
        src_glyph.draw(rec)
        rec.replay(tp)
    else:
        src_glyph.draw(tp)
    vf["glyf"].glyphs[vf_name] = pen.glyph()
    vf["hmtx"][vf_name] = (new_advance, int(round(new_lsb)))

    src_gvar = src_vf["gvar"]
    vf_gvar = vf["gvar"]
    if composite or src_name not in src_gvar.variations:
        if vf_name in vf_gvar.variations:
            del vf_gvar.variations[vf_name]
        return True, "static" if composite else "no-deltas"

    new_deltas = []
    for src_delta in src_gvar.variations[src_name]:
        new_deltas.append(
            TupleVariation(
                dict(src_delta.axes),
                scale_delta_coords(src_delta.coordinates, outline_scale),
            )
        )
    vf_gvar.variations[vf_name] = new_deltas
    return True, "variable"


def main() -> int:
    if not BASE_VF.exists() or not SOURCE_VF.exists():
        print("✗ Source files missing", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Building D-OPTICAL: outline=×{OUTLINE_SCALE:.4f}, side bearing factor={SIDE_BEARING_FACTOR} ({int((1-SIDE_BEARING_FACTOR)*100)}% tighter)")

    vf = TTFont(str(BASE_VF))
    src = TTFont(str(SOURCE_VF))
    src_cmap = src["cmap"].getBestCmap()
    vf_cmap = vf["cmap"].getBestCmap()

    counts = {"variable": 0, "static": 0, "no-deltas": 0, "empty": 0, "missing": 0}
    for start, end in LATIN_RANGES:
        for cp in range(start, end + 1):
            if cp not in src_cmap or cp not in vf_cmap:
                continue
            ok, status = replace_optical(
                vf, vf_cmap[cp], src, src_cmap[cp], OUTLINE_SCALE, SIDE_BEARING_FACTOR
            )
            if ok:
                counts[status] = counts.get(status, 0) + 1

    print(f"  variable (slider works):   {counts['variable']}")
    print(f"  static (composites):       {counts['static']}")
    print(f"  no-deltas (simple, fixed): {counts['no-deltas']}")
    print(f"  empty (space-like):        {counts['empty']}")

    nt = vf["name"]
    name = "Incruit Sans v04-D-optical"
    nt.setName(name, 1, 1, 0, 0); nt.setName(name, 1, 3, 1, 0x409)
    nt.setName(name, 4, 1, 0, 0); nt.setName(name, 4, 3, 1, 0x409)
    nt.setName("IncruitSans-v04Doptical", 6, 1, 0, 0)
    nt.setName("IncruitSans-v04Doptical", 6, 3, 1, 0x409)

    out_ttf = OUT_DIR / "IncruitSans-D-optical.ttf"
    vf.save(str(out_ttf))
    vf.flavor = "woff2"
    out_woff2 = OUT_DIR / "IncruitSans-D-optical.woff2"
    vf.save(str(out_woff2))

    print(f"\n  ✓ {out_ttf.name}")
    print(f"  ✓ {out_woff2.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
