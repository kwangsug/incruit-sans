#!/usr/bin/env python3
"""
Incruit Sans v0.2 PoC — multi-variant scale comparison.

Builds 4 variants with different Latin scale factors to find the best
visual balance between Hangul and Latin glyphs.

Measured base ratios (Pretendard vs Source Sans 3 em-normalized):
- x-height:  +9.11% needed
- cap height: +7.78%
- 'o' height: +7.42%
- '0' height: +9.75%
- average:    ~8.5%

Variants: 1.00× (baseline), 1.05×, 1.09× (x-height match), 1.12× (slight overshoot)
"""
import sys
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform

PROJECT_ROOT = Path(__file__).parent.parent
PRETENDARD = PROJECT_ROOT / "src" / "pretendard-1.3.9" / "public" / "static" / "Pretendard-Regular.otf"
SOURCE_SANS = PROJECT_ROOT / "src" / "OTF" / "SourceSans3-Regular.otf"
OUT_DIR = PROJECT_ROOT / "build" / "v0.2-variants"

LATIN_RANGES: list[tuple[int, int]] = [
    (0x0020, 0x007E),
    (0x00A0, 0x00FF),
]

VARIANTS = [
    ("A-baseline", 1.00),
    ("B-1.05x", 1.05),
    ("C-xheight-match", 1.09),
    ("D-1.12x", 1.12),
]


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


def build_variant(label: str, extra_scale: float) -> Path:
    pretendard = TTFont(str(PRETENDARD))
    source_sans = TTFont(str(SOURCE_SANS))

    em_scale = pretendard["head"].unitsPerEm / source_sans["head"].unitsPerEm
    final_scale = em_scale * extra_scale

    src_cmap = source_sans["cmap"].getBestCmap()
    dst_cmap = pretendard["cmap"].getBestCmap()

    replaced = 0
    for start, end in LATIN_RANGES:
        for cp in range(start, end + 1):
            if cp not in src_cmap or cp not in dst_cmap:
                continue
            if replace_glyph(pretendard, dst_cmap[cp], source_sans, src_cmap[cp], final_scale):
                replaced += 1

    nt = pretendard["name"]
    name_str = f"Incruit Sans v02-{label}"
    ps_name = f"IncruitSans-v02{label.replace('-', '')}"
    nt.setName(name_str, 1, 1, 0, 0)
    nt.setName(name_str, 1, 3, 1, 0x409)
    nt.setName(name_str, 4, 1, 0, 0)
    nt.setName(name_str, 4, 3, 1, 0x409)
    nt.setName(ps_name, 6, 1, 0, 0)
    nt.setName(ps_name, 6, 3, 1, 0x409)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    otf_path = OUT_DIR / f"IncruitSans-{label}.otf"
    pretendard.save(str(otf_path))

    pretendard.flavor = "woff2"
    woff2_path = OUT_DIR / f"IncruitSans-{label}.woff2"
    pretendard.save(str(woff2_path))

    print(f"  ✓ {label:20s} scale={final_scale:.4f} ({extra_scale:.2f}× extra)  glyphs={replaced}")
    return otf_path


def main() -> int:
    print(f"Building v0.2 variants → {OUT_DIR}")
    for label, extra in VARIANTS:
        build_variant(label, extra)
    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
