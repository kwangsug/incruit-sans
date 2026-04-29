#!/usr/bin/env python3
"""
Incruit Sans v0.5 — Composite-aware VF Latin merge with weight remap.

Fixes v0.4 issues:
- "i 이상해": 'i', 'j', and 76 Latin-1 composite glyphs were decomposed and lost
  variation. v0.5 preserves composite structure + transplants components.
- Weight mismatch: applies W2-target shift (+0.16 normalized) to all gvar deltas
  including composite component shifts.

Strategy:
1. Pass A — Transplant simple base glyphs (115 codepoints, like v0.4)
2. Pass B — Transplant diacritic/special components (uni0300, uni0301, dotlessi,
            etc.) as new simple glyphs in our VF (named with `_ss3_` prefix to
            avoid collision)
3. Pass C — For composite Latin glyphs (76 codepoints), build composite structure
            using component names (some prefixed, some unchanged like 'A', 'a'),
            with scaled offsets and transplanted gvar deltas.

Output: build/v0.5-vf/IncruitSans-Variable.ttf + .woff2
"""
import sys
import shutil
from copy import deepcopy
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphComponent, OVERLAP_COMPOUND
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform

PROJECT_ROOT = Path(__file__).parent.parent
BASE_VF = PROJECT_ROOT / "build" / "v0.2-vf" / "IncruitSans-Variable.ttf"
SOURCE_VF = PROJECT_ROOT / "src" / "source-sans-vf" / "VF" / "SourceSans3VF-Upright.ttf"
OUT_DIR = PROJECT_ROOT / "build" / "v0.5-vf"

OUTLINE_SCALE = 2.048 * 1.09
WEIGHT_SHIFT_NORM = 0.16

LATIN_RANGES = [(0x0020, 0x007E), (0x00A0, 0x00FF)]
COMPONENT_PREFIX = "_ss3_"

VERSION = "0.5.0"


def is_composite(font, name):
    glyf = font["glyf"]
    if name not in glyf.glyphs:
        return False
    g = glyf[name]
    return getattr(g, "isComposite", lambda: False)()


def scale_delta_coords(coords, scale):
    return [
        None if c is None else (int(round(c[0] * scale)), int(round(c[1] * scale)))
        for c in coords
    ]


def remap_axes(src_axes: dict, shift_norm: float) -> dict:
    new_axes = {}
    for axis_tag, (start, peak, end) in src_axes.items():
        if axis_tag == "wght":
            new_start = max(start + shift_norm, -1.0)
            if peak > new_start:
                new_start = min(new_start, peak - 0.001)
            new_axes[axis_tag] = (new_start, peak, end)
        else:
            new_axes[axis_tag] = (start, peak, end)
    return new_axes


def transplant_simple_glyph_with_deltas(
    vf: TTFont, dst_name: str,
    src_vf: TTFont, src_name: str,
    scale: float, shift_norm: float,
    add_to_cmap_codepoint: int | None = None,
) -> bool:
    """Copy a simple (non-composite) glyph from src to vf, scaling outlines and deltas.
    If dst_name doesn't exist in vf, append to glyph order."""
    src_glyph_set = src_vf.getGlyphSet()
    if src_name not in src_glyph_set:
        return False

    src_glyph = src_glyph_set[src_name]
    new_advance = int(round(src_glyph.width * scale))

    pen = TTGlyphPen(None)
    tp = TransformPen(pen, Transform(scale, 0, 0, scale, 0, 0))
    src_glyph.draw(tp)
    new_ttglyph = pen.glyph()

    glyph_order = vf.getGlyphOrder()
    if dst_name not in vf["glyf"].glyphs:
        glyph_order = list(glyph_order) + [dst_name]
        vf.setGlyphOrder(glyph_order)
        vf["maxp"].numGlyphs = len(glyph_order)

    vf["glyf"].glyphs[dst_name] = new_ttglyph

    src_lsb = src_vf["hmtx"][src_name][1] if src_name in src_vf["hmtx"].metrics else 0
    new_lsb = int(round(src_lsb * scale))
    vf["hmtx"][dst_name] = (new_advance, new_lsb)

    src_gvar = src_vf["gvar"]
    vf_gvar = vf["gvar"]
    if src_name in src_gvar.variations:
        new_deltas = []
        for src_delta in src_gvar.variations[src_name]:
            new_deltas.append(
                TupleVariation(
                    remap_axes(src_delta.axes, shift_norm),
                    scale_delta_coords(src_delta.coordinates, scale),
                )
            )
        vf_gvar.variations[dst_name] = new_deltas
    elif dst_name in vf_gvar.variations:
        del vf_gvar.variations[dst_name]
    return True


def collect_latin_composites(src_vf: TTFont) -> tuple[list, set]:
    """Return (list of (codepoint, src_glyph_name) for composites, set of all components used)."""
    cmap = src_vf["cmap"].getBestCmap()
    glyf = src_vf["glyf"]
    composites = []
    components = set()
    for start, end in LATIN_RANGES:
        for cp in range(start, end + 1):
            if cp not in cmap:
                continue
            gname = cmap[cp]
            if is_composite(src_vf, gname):
                composites.append((cp, gname))
                for comp in glyf[gname].components:
                    components.add(comp.glyphName)
    return composites, components


def build_composite_glyph(
    vf: TTFont, vf_name: str,
    src_vf: TTFont, src_name: str,
    component_name_map: dict,
    scale: float, shift_norm: float,
) -> bool:
    """Build composite glyph in vf from scratch (no deepcopy of source) to avoid
    stale `data` attribute that holds binary references to source glyph IDs."""
    src_glyph = src_vf["glyf"][src_name]
    if not getattr(src_glyph, "isComposite", lambda: False)():
        return False

    new_glyph = Glyph()
    new_glyph.numberOfContours = -1
    new_glyph.components = []

    for src_comp in src_glyph.components:
        mapped_name = component_name_map.get(src_comp.glyphName, src_comp.glyphName)
        if mapped_name not in vf["glyf"].glyphs:
            return False
        new_comp = GlyphComponent()
        new_comp.glyphName = mapped_name
        new_comp.flags = int(src_comp.flags) & ~OVERLAP_COMPOUND
        if hasattr(src_comp, "x"):
            new_comp.x = int(round(src_comp.x * scale))
            new_comp.y = int(round(src_comp.y * scale))
        else:
            new_comp.x = 0
            new_comp.y = 0
        if hasattr(src_comp, "firstPt"):
            new_comp.firstPt = src_comp.firstPt
            new_comp.secondPt = src_comp.secondPt
        if hasattr(src_comp, "transform"):
            new_comp.transform = [list(row) for row in src_comp.transform]
        new_glyph.components.append(new_comp)

    vf["glyf"].glyphs[vf_name] = new_glyph

    src_advance = src_vf["hmtx"][src_name][0]
    src_lsb = src_vf["hmtx"][src_name][1]
    vf["hmtx"][vf_name] = (int(round(src_advance * scale)), int(round(src_lsb * scale)))

    src_gvar = src_vf["gvar"]
    vf_gvar = vf["gvar"]
    if src_name in src_gvar.variations:
        new_deltas = []
        for src_delta in src_gvar.variations[src_name]:
            new_deltas.append(
                TupleVariation(
                    remap_axes(src_delta.axes, shift_norm),
                    scale_delta_coords(src_delta.coordinates, scale),
                )
            )
        vf_gvar.variations[vf_name] = new_deltas
    elif vf_name in vf_gvar.variations:
        del vf_gvar.variations[vf_name]

    return True


def main() -> int:
    if not BASE_VF.exists() or not SOURCE_VF.exists():
        print(f"✗ Source files missing", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"v0.5 composite-aware build")
    print(f"  outline scale: {OUTLINE_SCALE:.4f}")
    print(f"  weight shift:  {WEIGHT_SHIFT_NORM:+.4f} normalized")

    vf = TTFont(str(BASE_VF))
    src = TTFont(str(SOURCE_VF))
    src_cmap = src["cmap"].getBestCmap()
    vf_cmap = vf["cmap"].getBestCmap()

    composites, components_used = collect_latin_composites(src)
    print(f"\n  composite Latin glyphs: {len(composites)}")
    print(f"  unique components needed: {len(components_used)}")

    print(f"\n[Pass A] Simple Latin glyphs (non-composite, in cmap)")
    pass_a_count = 0
    for start, end in LATIN_RANGES:
        for cp in range(start, end + 1):
            if cp not in src_cmap or cp not in vf_cmap:
                continue
            src_name = src_cmap[cp]
            if is_composite(src, src_name):
                continue
            if transplant_simple_glyph_with_deltas(
                vf, vf_cmap[cp], src, src_name, OUTLINE_SCALE, WEIGHT_SHIFT_NORM
            ):
                pass_a_count += 1
    print(f"  ✓ {pass_a_count} simple glyphs transplanted with variable deltas")

    print(f"\n[Pass B] Component glyphs (diacritics + special)")
    component_name_map: dict[str, str] = {}
    pass_b_count = 0
    pass_b_skipped = 0
    for src_comp_name in sorted(components_used):
        if src_comp_name in vf_cmap.values():
            component_name_map[src_comp_name] = src_comp_name
            pass_b_skipped += 1
            continue
        new_name = COMPONENT_PREFIX + src_comp_name
        if transplant_simple_glyph_with_deltas(
            vf, new_name, src, src_comp_name, OUTLINE_SCALE, WEIGHT_SHIFT_NORM
        ):
            component_name_map[src_comp_name] = new_name
            pass_b_count += 1
    print(f"  ✓ {pass_b_count} new component glyphs transplanted (with `{COMPONENT_PREFIX}` prefix)")
    print(f"  ✓ {pass_b_skipped} components reuse existing Latin glyphs in our VF")

    print(f"\n[Pass C] Composite Latin glyphs (preserve composite structure)")
    pass_c_count = 0
    pass_c_failed = 0
    for cp, src_name in composites:
        if cp not in vf_cmap:
            continue
        if build_composite_glyph(vf, vf_cmap[cp], src, src_name, component_name_map, OUTLINE_SCALE, WEIGHT_SHIFT_NORM):
            pass_c_count += 1
        else:
            pass_c_failed += 1
    print(f"  ✓ {pass_c_count} composite Latin glyphs built with variable component shifts")
    if pass_c_failed:
        print(f"  ✗ {pass_c_failed} failed")

    nt = vf["name"]
    name = f"Incruit Sans"
    full = f"{name} Variable"
    nt.setName(
        f"Copyright (c) 2026 Incruit Corp. "
        f"Hangul: Pretendard Variable (OFL 1.1, Kil Hyung-jin). "
        f"Latin: Source Sans 3 VF (OFL 1.1, Adobe / Paul D. Hunt).",
        0, 1, 0, 0,
    )
    nt.setName(
        f"Copyright (c) 2026 Incruit Corp. "
        f"Hangul: Pretendard Variable (OFL 1.1, Kil Hyung-jin). "
        f"Latin: Source Sans 3 VF (OFL 1.1, Adobe / Paul D. Hunt).",
        0, 3, 1, 0x409,
    )
    nt.setName(f"Version {VERSION}", 5, 1, 0, 0)
    nt.setName(f"Version {VERSION}", 5, 3, 1, 0x409)

    composites_now = {}
    for gn in vf.getGlyphOrder():
        g = vf["glyf"].glyphs.get(gn)
        if g is None:
            continue
        if getattr(g, "isComposite", lambda: False)():
            if hasattr(g, "components") and g.components:
                composites_now[gn] = [c.glyphName for c in g.components]
    print(f"\n  composites in vf before save: {len(composites_now)}")
    cycle_found = None
    for start in composites_now:
        stack = [(start, [start])]
        while stack:
            node, path = stack.pop()
            for child in composites_now.get(node, []):
                if child in path:
                    cycle_found = path[path.index(child):] + [child]
                    break
                if child in composites_now:
                    stack.append((child, path + [child]))
            if cycle_found:
                break
        if cycle_found:
            break
    if cycle_found:
        print(f"  ❌ CYCLE: {' → '.join(cycle_found[:6])}{'...' if len(cycle_found)>6 else ''}")
    else:
        print(f"  ✅ no cycles")

    missing_refs = []
    for gn, comps in composites_now.items():
        for c in comps:
            if c not in vf["glyf"].glyphs:
                missing_refs.append((gn, c))
    if missing_refs:
        print(f"  ❌ {len(missing_refs)} missing component refs (sample): {missing_refs[:5]}")

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

    print(f"\n✓ v0.5 build complete → {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
