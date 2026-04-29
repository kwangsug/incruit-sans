#!/usr/bin/env python3
"""
Incruit Sans v1.0 (revised) — Pretendard 단순 리브랜드.

Latin 결합 시도 (SS3 / Open Sans / Roboto / Min Sans)를 모두 평가한 결과,
**Pretendard 자체 디자인이 한글-Latin 균형 가장 자연스러움** 결론.

Latin 결합 한계:
- 모든 외부 Latin 베이스에서 한글 옆 stroke·자간 미스매치 발견
- composite 글리프 (i, j, 악센트) VF 가변 보존 실패 → 78~60자 static
- Pretendard의 Latin은 Hangul과 함께 검증된 일체형 디자인

채택: Pretendard 통째 리브랜드 + tnum 기본화 + 메타데이터 정정.

Outputs:
- Variable Font: Pretendard Variable → IncruitSans-Variable.{ttf,woff2}
- Static OTF: Pretendard {Light,Regular,Medium,Bold}.otf → IncruitSans-{...}.otf
- Static TTF: cu2qu 변환 + ttfautohint
"""
import sys
import shutil
import subprocess
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.ttLib.tables._g_l_y_f import table__g_l_y_f
from fontTools.ttLib.tables._l_o_c_a import table__l_o_c_a
from fontTools.ttLib.tables._m_a_x_p import table__m_a_x_p

PROJECT_ROOT = Path(__file__).parent.parent
PRETENDARD_DIR = PROJECT_ROOT / "src" / "pretendard-1.3.9" / "public"
PRETENDARD_VF = PRETENDARD_DIR / "variable" / "PretendardVariable.ttf"
PRETENDARD_STATIC = PRETENDARD_DIR / "static"

OUT_DIR = PROJECT_ROOT / "build" / "v1.0"
STATIC_DIR = OUT_DIR / "static"

VERSION = "1.0.0"
FAMILY = "Incruit Sans"
TTFAUTOHINT = shutil.which("ttfautohint")

WEIGHT_MAP = {
    "Light": ("Pretendard-Light.otf", 300),
    "Regular": ("Pretendard-Regular.otf", 400),
    "Medium": ("Pretendard-Medium.otf", 500),
    "Bold": ("Pretendard-Bold.otf", 700),
}


def set_name(nt, nid, value):
    nt.setName(value, nid, 1, 0, 0)
    nt.setName(value, nid, 3, 1, 0x409)


def clean_names(font, full_name, version, postscript_name, subfamily="Regular", typo_subfamily=None):
    nt = font["name"]
    for nid in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 16, 17, 21, 22, 25]:
        nt.removeNames(nameID=nid)

    copyright_text = (
        "Copyright (c) 2026 Incruit Corp. "
        "Based on Pretendard (Copyright 2021 Kil Hyung-jin), licensed under SIL Open Font License 1.1."
    )
    designer_text = "Incruit AX Office (based on Pretendard by Kil Hyung-jin)."
    license_desc = "This Font Software is licensed under the SIL Open Font License, Version 1.1."

    is_bold = subfamily == "Bold"
    is_regular_subfam = subfamily == "Regular" and typo_subfamily is None

    if is_bold or is_regular_subfam:
        family = FAMILY
        typo_family = None
    else:
        display_subfam = typo_subfamily or subfamily
        family = f"{FAMILY} {display_subfam}"
        typo_family = FAMILY

    set_name(nt, 0, copyright_text)
    set_name(nt, 1, family)
    set_name(nt, 2, "Bold" if is_bold else "Regular")
    set_name(nt, 3, f"Incruit Corp.: {full_name}: {version}")
    set_name(nt, 4, full_name)
    set_name(nt, 5, f"Version {version}")
    set_name(nt, 6, postscript_name)
    set_name(nt, 7, "Incruit Sans is a trademark of Incruit Corp.")
    set_name(nt, 8, "Incruit Corp.")
    set_name(nt, 9, designer_text)
    set_name(nt, 11, "https://www.incruit.com")
    set_name(nt, 13, license_desc)
    set_name(nt, 14, "https://openfontlicense.org")
    if typo_family and typo_subfamily:
        set_name(nt, 16, typo_family)
        set_name(nt, 17, typo_subfamily)


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


def build_vf():
    print(f"\n[1/3] Variable Font (Pretendard Variable rebrand)")
    f = TTFont(str(PRETENDARD_VF))
    activate_tnum(f)
    clean_names(f, f"{FAMILY} Variable", VERSION, "IncruitSans-Variable", "Regular", "Variable")

    out_ttf = OUT_DIR / "IncruitSans-Variable.ttf"
    f.save(str(out_ttf))
    print(f"  ✓ {out_ttf.name} ({out_ttf.stat().st_size / (1024*1024):.1f}M)")

    f.flavor = "woff2"
    out_woff2 = OUT_DIR / "IncruitSans-Variable.woff2"
    f.save(str(out_woff2))
    print(f"  ✓ {out_woff2.name} ({out_woff2.stat().st_size / 1024:.0f}K)")


def cff_to_ttf(font: TTFont) -> TTFont:
    glyph_set = font.getGlyphSet()
    glyph_order = font.getGlyphOrder()
    new_glyphs = {}
    for gname in glyph_order:
        pen = TTGlyphPen(None)
        cu2qu_pen = Cu2QuPen(pen, max_err=1.0, reverse_direction=True)
        glyph_set[gname].draw(cu2qu_pen)
        new_glyphs[gname] = pen.glyph()

    glyf_table = table__g_l_y_f()
    glyf_table.glyphs = new_glyphs
    glyf_table.glyphOrder = glyph_order
    font["glyf"] = glyf_table
    font["loca"] = table__l_o_c_a()

    new_maxp = table__m_a_x_p()
    new_maxp.tableVersion = 0x00010000
    new_maxp.numGlyphs = len(glyph_order)
    for attr in ["maxPoints", "maxContours", "maxCompositePoints", "maxCompositeContours",
                 "maxZones", "maxTwilightPoints", "maxStorage", "maxFunctionDefs",
                 "maxInstructionDefs", "maxStackElements", "maxSizeOfInstructions",
                 "maxComponentElements", "maxComponentDepth"]:
        setattr(new_maxp, attr, 0)
    new_maxp.maxZones = 2
    font["maxp"] = new_maxp

    if "CFF " in font:
        del font["CFF "]
    font.sfntVersion = "\x00\x01\x00\x00"
    font["head"].indexToLocFormat = 1
    font["head"].glyphDataFormat = 0
    return font


def autohint(ttf_path: Path) -> bool:
    if not TTFAUTOHINT:
        return False
    tmp = ttf_path.with_suffix(".hinted.ttf")
    result = subprocess.run(
        [
            TTFAUTOHINT, "--no-info", "--composites",
            "--default-script=latn", "--fallback-script=latn",
            "--hinting-range-min=8", "--hinting-range-max=72",
            str(ttf_path), str(tmp),
        ],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return False
    shutil.move(str(tmp), str(ttf_path))
    return True


def build_static():
    print(f"\n[2/3] Static OTF (Pretendard rebrand)")
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

    for label, (filename, wght) in WEIGHT_MAP.items():
        src = PRETENDARD_STATIC / filename
        if not src.exists():
            print(f"  ✗ {filename} not found")
            continue
        f = TTFont(str(src))
        activate_tnum(f)
        full_name = f"{FAMILY} {label}"
        ps_name = f"IncruitSans-{label}"
        typo_subfam = None if label in ("Regular", "Bold") else label
        clean_names(f, full_name, VERSION, ps_name, label, typo_subfam)

        out_otf = STATIC_DIR / f"IncruitSans-{label}.otf"
        f.save(str(out_otf))

        f2 = TTFont(str(out_otf))
        f2.flavor = "woff2"
        out_woff2 = STATIC_DIR / f"IncruitSans-{label}.woff2"
        f2.save(str(out_woff2))
        print(f"  ✓ {label:8s} (wght {wght}) → otf {out_otf.stat().st_size//1024}K, woff2 {out_woff2.stat().st_size//1024}K")


def build_static_ttf():
    print(f"\n[3/3] Static TTF (cu2qu + ttfautohint)")
    ttf_dir = STATIC_DIR / "ttf"
    ttf_dir.mkdir(parents=True, exist_ok=True)

    for label, (filename, wght) in WEIGHT_MAP.items():
        src = PRETENDARD_STATIC / filename
        if not src.exists():
            continue
        f = TTFont(str(src))
        f = cff_to_ttf(f)
        activate_tnum(f)
        full_name = f"{FAMILY} {label}"
        ps_name = f"IncruitSans-{label}"
        typo_subfam = None if label in ("Regular", "Bold") else label
        clean_names(f, full_name, VERSION, ps_name, label, typo_subfam)

        out_ttf = ttf_dir / f"IncruitSans-{label}.ttf"
        f.save(str(out_ttf))
        hinted = autohint(out_ttf)

        f2 = TTFont(str(out_ttf))
        f2.flavor = "woff2"
        out_woff2 = ttf_dir / f"IncruitSans-{label}.woff2"
        f2.save(str(out_woff2))
        print(f"  ✓ {label:8s} → ttf {out_ttf.stat().st_size//1024}K, woff2 {out_woff2.stat().st_size//1024}K  [{'hinted ✅' if hinted else 'no hint'}]")


def main():
    if not PRETENDARD_VF.exists():
        print(f"✗ Pretendard VF missing: {PRETENDARD_VF}", file=sys.stderr)
        return 1

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    print(f"Incruit Sans v{VERSION} — Pretendard 단순 리브랜드")
    print(f"  ttfautohint: {'available' if TTFAUTOHINT else 'NOT available'}")

    build_vf()
    build_static()
    build_static_ttf()

    license_src = PROJECT_ROOT / "src" / "pretendard-1.3.9" / "LICENSE.txt"
    if license_src.exists():
        shutil.copy(license_src, OUT_DIR / "OFL.txt")
        shutil.copy(license_src, STATIC_DIR / "OFL.txt")

    print(f"\n✓ v{VERSION} (Pretendard 리브랜드) build complete → {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
