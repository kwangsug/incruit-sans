#!/usr/bin/env python3
"""
Incruit Sans v0.4 — Latin weight correction variants.

Problem (measured):
  Source Sans 3 'l' stroke is 30-60% heavier than Pretendard 'l' at same wght.
  Most extreme at wght 400: SS3 134.7/1000 em vs Pretendard 84/1000 em (+60%).

Fix: Remap gvar delta tuples by shifting `start` value.
- Original SS3 delta: axes={'wght': (200, 900, 900)}
  → at our wght=400, scalar=(400-200)/(900-200)=0.286 → SS3 visual ≈ 400
- Shifted: axes={'wght': (NEW_START, 900, 900)}
  → at our wght=400, scalar smaller → less delta → SS3 visual lighter

Variants:
- W1 light:   shift +100 (start=300)  — gentle correction
- W2 target:  shift +160 (start=360)  — measurement-based, wght 400 matched
- W3 heavy:   shift +220 (start=420)  — over-correction (Latin lighter than Hangul)
"""
import sys
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
OUT_DIR = PROJECT_ROOT / "build" / "v0.4-weight-variants"

OUTLINE_SCALE = 2.048 * 1.09
LATIN_RANGES = [(0x0020, 0x007E), (0x00A0, 0x00FF)]

VARIANTS = [
    ("W0-noshift", 0.0),
    ("W1-light",   100.0 / 1000.0),
    ("W2-target",  160.0 / 1000.0),
    ("W3-heavy",   220.0 / 1000.0),
]


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


def remap_axes(src_axes: dict, shift_norm: float) -> dict:
    """Shift start value in normalized axis space (gvar uses normalized -1..1).
    SS3 wght 200 → -1 (start), 200 → 0 (default actually wght 200 is default for SS3),
    900 → +1 (end).
    Actually SS3 default is wght 200 → normalized 0. wght 900 → +1.
    Shifting start (originally 0) by +shift_norm.
    """
    new_axes = {}
    for axis_tag, (start, peak, end) in src_axes.items():
        if axis_tag == "wght":
            new_start = max(start + shift_norm, -1.0)
            new_start = min(new_start, peak - 0.001) if peak > new_start else new_start
            new_axes[axis_tag] = (new_start, peak, end)
        else:
            new_axes[axis_tag] = (start, peak, end)
    return new_axes


def replace_with_weight_remap(vf, vf_name, src_vf, src_name, scale, shift_norm):
    src_glyph_set = src_vf.getGlyphSet()
    if src_name not in src_glyph_set or vf_name not in vf["glyf"].glyphs:
        return False, False

    src_glyph = src_glyph_set[src_name]
    new_advance = int(round(src_glyph.width * scale))
    composite = is_composite(src_vf, src_name)

    pen = TTGlyphPen(None)
    tp = TransformPen(pen, Transform(scale, 0, 0, scale, 0, 0))
    if composite:
        rec = DecomposingRecordingPen(src_glyph_set)
        src_glyph.draw(rec)
        rec.replay(tp)
    else:
        src_glyph.draw(tp)
    vf["glyf"].glyphs[vf_name] = pen.glyph()

    lsb = vf["hmtx"][vf_name][1]
    vf["hmtx"][vf_name] = (new_advance, lsb)

    src_gvar = src_vf["gvar"]
    vf_gvar = vf["gvar"]
    if composite or src_name not in src_gvar.variations:
        if vf_name in vf_gvar.variations:
            del vf_gvar.variations[vf_name]
        return True, False

    new_deltas = []
    for src_delta in src_gvar.variations[src_name]:
        new_delta = TupleVariation(
            remap_axes(src_delta.axes, shift_norm),
            scale_delta_coords(src_delta.coordinates, scale),
        )
        new_deltas.append(new_delta)
    vf_gvar.variations[vf_name] = new_deltas
    return True, True


def build_variant(label: str, shift_norm: float):
    print(f"\n  Building {label}: gvar wght axis shift={shift_norm:+.4f} (normalized)")

    vf = TTFont(str(BASE_VF))
    src = TTFont(str(SOURCE_VF))
    src_cmap = src["cmap"].getBestCmap()
    vf_cmap = vf["cmap"].getBestCmap()

    replaced = 0
    with_deltas = 0
    for start, end in LATIN_RANGES:
        for cp in range(start, end + 1):
            if cp not in src_cmap or cp not in vf_cmap:
                continue
            ok, has_deltas = replace_with_weight_remap(
                vf, vf_cmap[cp], src, src_cmap[cp], OUTLINE_SCALE, shift_norm
            )
            if ok:
                replaced += 1
                if has_deltas:
                    with_deltas += 1

    nt = vf["name"]
    name = f"Incruit Sans v04-{label}"
    nt.setName(name, 1, 1, 0, 0); nt.setName(name, 1, 3, 1, 0x409)
    nt.setName(name, 4, 1, 0, 0); nt.setName(name, 4, 3, 1, 0x409)
    ps = f"IncruitSans-v04{label.replace('-', '')}"
    nt.setName(ps, 6, 1, 0, 0); nt.setName(ps, 6, 3, 1, 0x409)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_ttf = OUT_DIR / f"IncruitSans-{label}.ttf"
    vf.save(str(out_ttf))
    vf.flavor = "woff2"
    out_woff2 = OUT_DIR / f"IncruitSans-{label}.woff2"
    vf.save(str(out_woff2))
    print(f"    ✓ {out_ttf.name}  ({replaced} replaced, {with_deltas} with remapped deltas)")


def main() -> int:
    if not BASE_VF.exists() or not SOURCE_VF.exists():
        print("✗ Source files missing", file=sys.stderr)
        return 1
    print(f"Outline scale (fixed): {OUTLINE_SCALE:.4f}")
    for label, shift in VARIANTS:
        build_variant(label, shift)
    print(f"\n✓ Done → {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
