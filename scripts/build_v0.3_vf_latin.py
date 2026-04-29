#!/usr/bin/env python3
"""
Incruit Sans v0.3 — Variable Font with Source Sans 3 Latin merge.

Strategy:
- Base: Pretendard Variable (TTF/glyf-based VF, wght axis 45→930)
- Latin glyphs (191 codepoints in Basic Latin + Latin-1 Supplement):
  - Outline replaced with Source Sans 3 Regular (CFF→quadratic, scaled 2.232×)
  - gvar (delta) entries removed → Latin becomes static across all wght values

Trade-off documented:
- Hangul: full VF interpolation (Pretendard's gvar preserved)
- Latin: static Source Sans 3 Regular at every wght value
- Rationale: Source Sans 3 weights are not point-compatible across masters,
  so proper Latin VF interpolation requires either Source Sans 3 VF source
  or font engineer master matching (deferred to v0.4).

Output: build/v0.3-vf/IncruitSans-Variable.ttf + .woff2
"""
import sys
import shutil
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform

PROJECT_ROOT = Path(__file__).parent.parent
SOURCE_VF = PROJECT_ROOT / "build" / "v0.2-vf" / "IncruitSans-Variable.ttf"
SOURCE_SANS_REGULAR = PROJECT_ROOT / "src" / "OTF" / "SourceSans3-Regular.otf"
OUT_DIR = PROJECT_ROOT / "build" / "v0.3-vf"

X_HEIGHT_BOOST = 1.09

LATIN_RANGES: list[tuple[int, int]] = [
    (0x0020, 0x007E),
    (0x00A0, 0x00FF),
]

VERSION = "0.3.0"


def replace_latin_glyph(
    vf_font: TTFont,
    vf_glyph_name: str,
    src_font: TTFont,
    src_glyph_name: str,
    scale: float,
) -> bool:
    src_glyph_set = src_font.getGlyphSet()
    if src_glyph_name not in src_glyph_set:
        return False
    if vf_glyph_name not in vf_font["glyf"].glyphs:
        return False

    src_glyph = src_glyph_set[src_glyph_name]
    new_advance = int(round(src_glyph.width * scale))

    pen = TTGlyphPen(None)
    cu2qu_pen = Cu2QuPen(pen, max_err=1.0, reverse_direction=True)
    transform_pen = TransformPen(cu2qu_pen, Transform(scale, 0, 0, scale, 0, 0))
    src_glyph.draw(transform_pen)
    new_ttglyph = pen.glyph()

    vf_font["glyf"].glyphs[vf_glyph_name] = new_ttglyph

    lsb = vf_font["hmtx"][vf_glyph_name][1]
    vf_font["hmtx"][vf_glyph_name] = (new_advance, lsb)

    if "gvar" in vf_font:
        gvar = vf_font["gvar"]
        if vf_glyph_name in gvar.variations:
            del gvar.variations[vf_glyph_name]

    if "HVAR" in vf_font:
        hvar = vf_font["HVAR"].table
        if hvar.AdvWidthMap is not None:
            mapping = hvar.AdvWidthMap.mapping
            if vf_glyph_name in mapping:
                pass

    return True


def main() -> int:
    if not SOURCE_VF.exists():
        print(f"✗ Base VF missing: {SOURCE_VF}", file=sys.stderr)
        print("  Run scripts/build_v0.2_ttf_vf.py first.", file=sys.stderr)
        return 1
    if not SOURCE_SANS_REGULAR.exists():
        print(f"✗ Source Sans 3 missing: {SOURCE_SANS_REGULAR}", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    vf = TTFont(str(SOURCE_VF))
    src = TTFont(str(SOURCE_SANS_REGULAR))

    em_scale = vf["head"].unitsPerEm / src["head"].unitsPerEm
    final_scale = em_scale * X_HEIGHT_BOOST
    print(f"Em scale: {src['head'].unitsPerEm} → {vf['head'].unitsPerEm} (× {em_scale}) "
          f"+ x-height boost {X_HEIGHT_BOOST}× = final {final_scale:.4f}")

    src_cmap = src["cmap"].getBestCmap()
    vf_cmap = vf["cmap"].getBestCmap()

    replaced = 0
    deltas_removed = 0
    failed: list[str] = []

    for start, end in LATIN_RANGES:
        for cp in range(start, end + 1):
            if cp not in src_cmap or cp not in vf_cmap:
                continue
            had_deltas = (
                "gvar" in vf and vf_cmap[cp] in vf["gvar"].variations
            )
            ok = replace_latin_glyph(vf, vf_cmap[cp], src, src_cmap[cp], final_scale)
            if ok:
                replaced += 1
                if had_deltas:
                    deltas_removed += 1
            else:
                failed.append(f"U+{cp:04X}")

    print(f"  Latin glyphs replaced:        {replaced}")
    print(f"  gvar deltas removed (Latin):  {deltas_removed} (Latin now static)")
    if failed:
        print(f"  Failed:                       {len(failed)} ({', '.join(failed[:10])}{'…' if len(failed) > 10 else ''})")

    nt = vf["name"]
    full = f"Incruit Sans Variable"
    nt.setName(
        "Copyright (c) 2026 Incruit Corp. "
        "Hangul (variable axis): based on Pretendard Variable (Copyright 2021 Kil Hyung-jin), OFL 1.1. "
        "Latin (static, Regular weight): based on Source Sans 3 Regular (Copyright 2010-2020 Adobe / Paul D. Hunt), OFL 1.1.",
        0, 1, 0, 0,
    )
    nt.setName(
        "Copyright (c) 2026 Incruit Corp. "
        "Hangul (variable axis): based on Pretendard Variable (Copyright 2021 Kil Hyung-jin), OFL 1.1. "
        "Latin (static, Regular weight): based on Source Sans 3 Regular (Copyright 2010-2020 Adobe / Paul D. Hunt), OFL 1.1.",
        0, 3, 1, 0x409,
    )
    nt.setName(f"Version {VERSION}", 5, 1, 0, 0)
    nt.setName(f"Version {VERSION}", 5, 3, 1, 0x409)
    nt.setName(
        "Incruit AX Office. "
        "Hangul: Pretendard Variable by Kil Hyung-jin. "
        "Latin: Source Sans 3 Regular by Paul D. Hunt / Adobe Type.",
        9, 1, 0, 0,
    )
    nt.setName(
        "Incruit AX Office. "
        "Hangul: Pretendard Variable by Kil Hyung-jin. "
        "Latin: Source Sans 3 Regular by Paul D. Hunt / Adobe Type.",
        9, 3, 1, 0x409,
    )

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

    print(f"\n✓ v0.3 VF build complete → {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
