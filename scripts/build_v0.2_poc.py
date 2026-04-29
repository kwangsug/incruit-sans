#!/usr/bin/env python3
"""
Incruit Sans v0.2 PoC — Source Sans 3 Latin glyph merge.

Status: PROOF OF CONCEPT (NOT PRODUCTION-READY)

This script demonstrates the v0.2 merge workflow for the font engineer hire:
1. Load Pretendard (base, em 2048) and Source Sans 3 (Latin source, em 1000)
2. For each Basic Latin codepoint, scale Source Sans 3 glyph by 2.048x
3. Replace the corresponding Pretendard glyph

Known limitations the engineer must address (see docs/v0.2-font-engineer-rfp.md):
- CFF charstring scaling via TransformPen may lose hinting nuance
- Glyph metrics (advance width, lsb) need post-merge verification
- GPOS kern from Source Sans 3 is NOT migrated (only outlines transplanted)
- Components/composites in Source Sans 3 are flattened
- Vertical metrics retained from Pretendard (intentional)
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
OUT_PATH = PROJECT_ROOT / "build" / "v0.2-poc" / "IncruitSans-Regular.otf"

LATIN_RANGES: list[tuple[int, int]] = [
    (0x0020, 0x007E),
    (0x00A0, 0x00FF),
]


def replace_glyph(dst_font: TTFont, dst_glyph_name: str, src_font: TTFont, src_glyph_name: str, scale: float) -> bool:
    """Copy a glyph from src to dst with uniform scaling. Returns True on success."""
    src_glyph_set = src_font.getGlyphSet()
    dst_glyph_set = dst_font.getGlyphSet()
    if src_glyph_name not in src_glyph_set or dst_glyph_name not in dst_glyph_set:
        return False

    src_glyph = src_glyph_set[src_glyph_name]
    src_advance = src_glyph.width
    new_advance = int(round(src_advance * scale))

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


def main() -> int:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    pretendard = TTFont(str(PRETENDARD))
    source_sans = TTFont(str(SOURCE_SANS))

    src_em = source_sans["head"].unitsPerEm
    dst_em = pretendard["head"].unitsPerEm
    scale = dst_em / src_em
    print(f"Em scale: {src_em} → {dst_em} (factor {scale})")

    src_cmap = source_sans["cmap"].getBestCmap()
    dst_cmap = pretendard["cmap"].getBestCmap()

    replaced = 0
    skipped_missing_src = 0
    skipped_missing_dst = 0
    failed = 0

    for start, end in LATIN_RANGES:
        for cp in range(start, end + 1):
            if cp not in src_cmap:
                skipped_missing_src += 1
                continue
            if cp not in dst_cmap:
                skipped_missing_dst += 1
                continue
            src_name = src_cmap[cp]
            dst_name = dst_cmap[cp]
            if replace_glyph(pretendard, dst_name, source_sans, src_name, scale):
                replaced += 1
            else:
                failed += 1

    print(f"  Replaced: {replaced}")
    print(f"  Skipped (no src):  {skipped_missing_src}")
    print(f"  Skipped (no dst):  {skipped_missing_dst}")
    print(f"  Failed:   {failed}")

    pretendard.save(str(OUT_PATH))
    print(f"\nPoC output: {OUT_PATH}")
    print("⚠️  This is a PoC. Do NOT ship without font engineer review.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
