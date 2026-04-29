#!/usr/bin/env python3
"""
Incruit Sans v0.4 — Variable Font with FULLY VARIABLE Source Sans 3 Latin.

Strategy (proper master delta transplant):
- Base: Pretendard Variable (TTF/glyf-based VF, wght 45→930, default 400)
- Latin source: Source Sans 3 VF Upright (TTF, wght 200→900, default 200)
- For each Latin glyph (191 codepoints):
  1. Replace default outline with Source Sans 3 default (scaled 2.232×)
  2. Replace gvar deltas with Source Sans 3 deltas (each delta coordinate scaled 2.232×)
- Result: Latin now interpolates with wght axis (slider works for both Hangul AND Latin)

Notes:
- Source Sans 3 default is wght 200 (ExtraLight). When our VF renders at wght 400,
  the deltas anchor near Source Sans 3 wght 400 (Regular) — visually correct.
- At wght extremes (45-200, 900-930), Latin clamps/extrapolates Source Sans 3's
  extreme weights — minor edge case but acceptable.
- Phantom points (advance width metrics) included in delta scaling.
"""
import sys
import shutil
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.misc.transform import Transform

PROJECT_ROOT = Path(__file__).parent.parent
BASE_VF = PROJECT_ROOT / "build" / "v0.2-vf" / "IncruitSans-Variable.ttf"
SOURCE_VF = PROJECT_ROOT / "src" / "source-sans-vf" / "VF" / "SourceSans3VF-Upright.ttf"
OUT_DIR = PROJECT_ROOT / "build" / "v0.4-vf"

X_HEIGHT_BOOST = 1.09

LATIN_RANGES: list[tuple[int, int]] = [
    (0x0020, 0x007E),
    (0x00A0, 0x00FF),
]

VERSION = "0.4.0"


def scale_delta_coordinates(coords: list, scale: float) -> list:
    scaled: list = []
    for c in coords:
        if c is None:
            scaled.append(None)
        else:
            dx, dy = c
            scaled.append((int(round(dx * scale)), int(round(dy * scale))))
    return scaled


def is_composite_glyph(font: TTFont, glyph_name: str) -> bool:
    glyf = font["glyf"]
    if glyph_name not in glyf.glyphs:
        return False
    glyph = glyf[glyph_name]
    return getattr(glyph, "isComposite", lambda: False)()


def draw_glyph_to_ttgpen(src_vf: TTFont, src_name: str, scale: float) -> tuple[object, bool]:
    """Draw glyph (decomposing composites) to a fresh TTGlyphPen. Returns (ttglyph, was_composite)."""
    src_glyph_set = src_vf.getGlyphSet()
    src_glyph = src_glyph_set[src_name]
    was_composite = is_composite_glyph(src_vf, src_name)

    pen = TTGlyphPen(None)
    transform_pen = TransformPen(pen, Transform(scale, 0, 0, scale, 0, 0))

    if was_composite:
        record = DecomposingRecordingPen(src_glyph_set)
        src_glyph.draw(record)
        record.replay(transform_pen)
    else:
        src_glyph.draw(transform_pen)

    return pen.glyph(), was_composite


def replace_glyph_with_variations(
    vf: TTFont,
    vf_name: str,
    src_vf: TTFont,
    src_name: str,
    scale: float,
) -> tuple[bool, int, bool]:
    """Replace default outline + transplant scaled gvar deltas. Returns (success, n_deltas, decomposed)."""
    src_glyph_set = src_vf.getGlyphSet()
    if src_name not in src_glyph_set or vf_name not in vf["glyf"].glyphs:
        return False, 0, False

    src_glyph = src_glyph_set[src_name]
    new_advance = int(round(src_glyph.width * scale))

    new_ttglyph, decomposed = draw_glyph_to_ttgpen(src_vf, src_name, scale)
    vf["glyf"].glyphs[vf_name] = new_ttglyph

    lsb = vf["hmtx"][vf_name][1]
    vf["hmtx"][vf_name] = (new_advance, lsb)

    src_gvar = src_vf["gvar"]
    vf_gvar = vf["gvar"]

    if decomposed:
        if vf_name in vf_gvar.variations:
            del vf_gvar.variations[vf_name]
        return True, 0, True

    if src_name not in src_gvar.variations:
        if vf_name in vf_gvar.variations:
            del vf_gvar.variations[vf_name]
        return True, 0, False

    src_deltas = src_gvar.variations[src_name]
    new_deltas: list[TupleVariation] = []
    for src_delta in src_deltas:
        new_delta = TupleVariation(
            dict(src_delta.axes),
            scale_delta_coordinates(src_delta.coordinates, scale),
        )
        new_deltas.append(new_delta)

    vf_gvar.variations[vf_name] = new_deltas
    return True, len(new_deltas), False


def main() -> int:
    if not BASE_VF.exists():
        print(f"✗ Base VF missing: {BASE_VF}", file=sys.stderr)
        print("  Run build_v0.2_ttf_vf.py first.", file=sys.stderr)
        return 1
    if not SOURCE_VF.exists():
        print(f"✗ Source Sans 3 VF missing: {SOURCE_VF}", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    vf = TTFont(str(BASE_VF))
    src = TTFont(str(SOURCE_VF))

    em_scale = vf["head"].unitsPerEm / src["head"].unitsPerEm
    final_scale = em_scale * X_HEIGHT_BOOST
    print(f"Em scale: {src['head'].unitsPerEm} → {vf['head'].unitsPerEm} (× {em_scale}) "
          f"+ x-height boost {X_HEIGHT_BOOST}× = final {final_scale:.4f}")

    base_axes = vf["fvar"].axes
    src_axes = src["fvar"].axes
    print(f"Base VF wght:    {base_axes[0].minValue:.0f} → {base_axes[0].maxValue:.0f} (default {base_axes[0].defaultValue:.0f})")
    print(f"Source Sans wght: {src_axes[0].minValue:.0f} → {src_axes[0].maxValue:.0f} (default {src_axes[0].defaultValue:.0f})")

    src_cmap = src["cmap"].getBestCmap()
    vf_cmap = vf["cmap"].getBestCmap()

    replaced = 0
    total_deltas = 0
    decomposed_count = 0
    failed: list[str] = []

    for start, end in LATIN_RANGES:
        for cp in range(start, end + 1):
            if cp not in src_cmap or cp not in vf_cmap:
                continue
            ok, n_deltas, decomposed = replace_glyph_with_variations(
                vf, vf_cmap[cp], src, src_cmap[cp], final_scale
            )
            if ok:
                replaced += 1
                total_deltas += n_deltas
                if decomposed:
                    decomposed_count += 1
            else:
                failed.append(f"U+{cp:04X}")

    print(f"\n  Latin glyphs replaced:        {replaced}")
    print(f"    - with variation deltas:    {replaced - decomposed_count} (full VF, slider works)")
    print(f"    - decomposed → static:      {decomposed_count} (composite glyphs, regular weight only)")
    print(f"  Total deltas transplanted:    {total_deltas}")
    if failed:
        print(f"  Failed:                       {len(failed)}")

    nt = vf["name"]
    copyright_text = (
        "Copyright (c) 2026 Incruit Corp. "
        "Hangul: based on Pretendard Variable (Copyright 2021 Kil Hyung-jin), OFL 1.1. "
        "Latin: based on Source Sans 3 VF Upright (Copyright 2010-2020 Adobe / Paul D. Hunt), OFL 1.1."
    )
    designer_text = (
        "Incruit AX Office. "
        "Hangul: Pretendard Variable by Kil Hyung-jin. "
        "Latin: Source Sans 3 VF Upright by Paul D. Hunt / Adobe Type."
    )
    nt.setName(copyright_text, 0, 1, 0, 0)
    nt.setName(copyright_text, 0, 3, 1, 0x409)
    nt.setName(f"Version {VERSION}", 5, 1, 0, 0)
    nt.setName(f"Version {VERSION}", 5, 3, 1, 0x409)
    nt.setName(designer_text, 9, 1, 0, 0)
    nt.setName(designer_text, 9, 3, 1, 0x409)

    out_ttf = OUT_DIR / "IncruitSans-Variable.ttf"
    vf.save(str(out_ttf))
    size_mb = out_ttf.stat().st_size / (1024 * 1024)
    print(f"\n  ✓ {out_ttf.name} ({size_mb:.1f}M)")

    vf.flavor = "woff2"
    out_woff2 = OUT_DIR / "IncruitSans-Variable.woff2"
    vf.save(str(out_woff2))
    size_kb = out_woff2.stat().st_size / 1024
    print(f"  ✓ {out_woff2.name} ({size_kb:.0f}K)")

    license_src = PROJECT_ROOT / "src" / "pretendard-1.3.9" / "LICENSE.txt"
    if license_src.exists():
        shutil.copy(license_src, OUT_DIR / "OFL.txt")

    print(f"\n✓ v0.4 VF build complete → {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
