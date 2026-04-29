#!/usr/bin/env python3
"""
Incruit Sans v0.4 — Latin advance width variant builder.

Builds 4 variants with different Latin advance width factors to find
optimal letter spacing balance with Hangul.

Outline scale: 2.2323 (em + x-height match) — fixed
Advance scale: outline_scale × {0.92, 0.94, 0.96, 0.98}

Lower advance factor = tighter Latin spacing = closer to Hangul density.
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
OUT_DIR = PROJECT_ROOT / "build" / "v0.4-advance-variants"

OUTLINE_SCALE_BASE = 2.048 * 1.09  # = 2.2323
LATIN_RANGES = [(0x0020, 0x007E), (0x00A0, 0x00FF)]

VARIANTS = [
    ("A-tight92", 0.92),
    ("B-094", 0.94),
    ("C-096", 0.96),
    ("D-098", 0.98),
]


def is_composite_glyph(font: TTFont, glyph_name: str) -> bool:
    glyf = font["glyf"]
    if glyph_name not in glyf.glyphs:
        return False
    return getattr(glyf[glyph_name], "isComposite", lambda: False)()


def scale_delta_coords(coords, scale):
    out = []
    for c in coords:
        if c is None:
            out.append(None)
        else:
            dx, dy = c
            out.append((int(round(dx * scale)), int(round(dy * scale))))
    return out


def replace_latin(vf, vf_name, src_vf, src_name, outline_scale, advance_scale):
    src_glyph_set = src_vf.getGlyphSet()
    if src_name not in src_glyph_set or vf_name not in vf["glyf"].glyphs:
        return False

    src_glyph = src_glyph_set[src_name]
    new_advance = int(round(src_glyph.width * advance_scale))
    is_composite = is_composite_glyph(src_vf, src_name)

    pen = TTGlyphPen(None)
    transform_pen = TransformPen(pen, Transform(outline_scale, 0, 0, outline_scale, 0, 0))
    if is_composite:
        record = DecomposingRecordingPen(src_glyph_set)
        src_glyph.draw(record)
        record.replay(transform_pen)
    else:
        src_glyph.draw(transform_pen)
    vf["glyf"].glyphs[vf_name] = pen.glyph()

    lsb = vf["hmtx"][vf_name][1]
    vf["hmtx"][vf_name] = (new_advance, lsb)

    src_gvar = src_vf["gvar"]
    vf_gvar = vf["gvar"]
    if is_composite or src_name not in src_gvar.variations:
        if vf_name in vf_gvar.variations:
            del vf_gvar.variations[vf_name]
        return True

    new_deltas = []
    for src_delta in src_gvar.variations[src_name]:
        new_deltas.append(
            TupleVariation(
                dict(src_delta.axes),
                scale_delta_coords(src_delta.coordinates, outline_scale),
            )
        )
    vf_gvar.variations[vf_name] = new_deltas
    return True


def build_variant(label: str, advance_factor: float):
    advance_scale = OUTLINE_SCALE_BASE * advance_factor
    print(f"\n  Building {label}: outline=×{OUTLINE_SCALE_BASE:.4f}, advance=×{advance_scale:.4f} (factor {advance_factor})")

    vf = TTFont(str(BASE_VF))
    src = TTFont(str(SOURCE_VF))
    src_cmap = src["cmap"].getBestCmap()
    vf_cmap = vf["cmap"].getBestCmap()

    count = 0
    for start, end in LATIN_RANGES:
        for cp in range(start, end + 1):
            if cp not in src_cmap or cp not in vf_cmap:
                continue
            if replace_latin(vf, vf_cmap[cp], src, src_cmap[cp], OUTLINE_SCALE_BASE, advance_scale):
                count += 1

    nt = vf["name"]
    name = f"Incruit Sans v04-{label}"
    nt.setName(name, 1, 1, 0, 0)
    nt.setName(name, 1, 3, 1, 0x409)
    nt.setName(name, 4, 1, 0, 0)
    nt.setName(name, 4, 3, 1, 0x409)
    nt.setName(f"IncruitSans-v04{label.replace('-', '')}", 6, 1, 0, 0)
    nt.setName(f"IncruitSans-v04{label.replace('-', '')}", 6, 3, 1, 0x409)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_ttf = OUT_DIR / f"IncruitSans-{label}.ttf"
    vf.save(str(out_ttf))

    vf.flavor = "woff2"
    out_woff2 = OUT_DIR / f"IncruitSans-{label}.woff2"
    vf.save(str(out_woff2))

    print(f"    ✓ {out_ttf.name} ({count} glyphs replaced)")
    print(f"    ✓ {out_woff2.name}")


def main() -> int:
    if not BASE_VF.exists():
        print(f"✗ Base VF missing: {BASE_VF}", file=sys.stderr)
        return 1
    if not SOURCE_VF.exists():
        print(f"✗ Source Sans 3 VF missing: {SOURCE_VF}", file=sys.stderr)
        return 1

    print(f"Outline scale (fixed): {OUTLINE_SCALE_BASE:.4f} (em 2.048× × x-height boost 1.09×)")
    for label, factor in VARIANTS:
        build_variant(label, factor)
    print(f"\n✓ Done → {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
