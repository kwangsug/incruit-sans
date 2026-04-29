#!/usr/bin/env python3
"""
Incruit Sans v1.0 — production candidate.

Baseline: v0.7 D variant (Roboto Flex Latin + Latin delta × 0.70 reduction).
Reasoning:
- em == 2048 (Pretendard match, no scaling)
- Roboto Flex Latin with delta × 0.70 → restrained variation, best matches
  Pretendard at all weights per visual review
- 128 variable Latin glyphs, 60 composite static (i, j, accents)
- Latin advance × 1.0 (Roboto natural spacing)

Outputs:
1. Variable Font: build/v1.0/IncruitSans-Variable.{ttf,woff2}
2. Static instances: build/v1.0/static/
   - IncruitSans-Light.ttf (wght 300)
   - IncruitSans-Regular.ttf (wght 400)
   - IncruitSans-Medium.ttf (wght 500)
   - IncruitSans-Bold.ttf (wght 700)
   - + WOFF2 for each

All assets: tnum default activation, proper Incruit Sans branding, OFL attribution.
"""
import sys
import shutil
import subprocess
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

PROJECT_ROOT = Path(__file__).parent.parent
SOURCE_VF = PROJECT_ROOT / "build" / "v0.7-lighter-variants" / "IncruitSans-D-070.ttf"
OUT_DIR = PROJECT_ROOT / "build" / "v1.0"
STATIC_DIR = OUT_DIR / "static"

VERSION = "1.0.0"
FAMILY = "Incruit Sans"
TTFAUTOHINT = shutil.which("ttfautohint")

WEIGHT_INSTANCES = [
    ("Light", 300),
    ("Regular", 400),
    ("Medium", 500),
    ("Bold", 700),
]


def set_name(nt, nid, value):
    nt.setName(value, nid, 1, 0, 0)
    nt.setName(value, nid, 3, 1, 0x409)


def clean_names(font, full_name, version, postscript_name, subfamily="Regular"):
    nt = font["name"]
    for nid in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 16, 17, 21, 22, 25]:
        nt.removeNames(nameID=nid)

    copyright_text = (
        "Copyright (c) 2026 Incruit Corp. "
        "Hangul: Pretendard Variable (Copyright 2021 Kil Hyung-jin), OFL 1.1. "
        "Latin: Roboto Flex (Copyright 2017 Google / Christian Robertson, David Berlow), OFL 1.1."
    )
    designer_text = (
        "Incruit AX Office. "
        "Hangul: Pretendard Variable by Kil Hyung-jin. "
        "Latin: Roboto Flex by Christian Robertson, David Berlow / Google."
    )
    license_desc = "This Font Software is licensed under the SIL Open Font License, Version 1.1."

    is_bold = subfamily == "Bold"
    is_regular = subfamily == "Regular"
    if is_bold or is_regular:
        family = FAMILY
        typo_family = None
        typo_subfamily = None
    else:
        family = f"{FAMILY} {subfamily}"
        typo_family = FAMILY
        typo_subfamily = subfamily

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
    if typo_family:
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
    print(f"\n[1/2] Variable Font v{VERSION}")
    f = TTFont(str(SOURCE_VF))
    activate_tnum(f)
    clean_names(f, f"{FAMILY} Variable", VERSION, "IncruitSans-Variable", "Regular")
    nt = f["name"]
    set_name(nt, 16, FAMILY)
    set_name(nt, 17, "Variable")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_ttf = OUT_DIR / "IncruitSans-Variable.ttf"
    f.save(str(out_ttf))
    print(f"  ✓ {out_ttf.name} ({out_ttf.stat().st_size / (1024*1024):.1f}M)")

    f.flavor = "woff2"
    out_woff2 = OUT_DIR / "IncruitSans-Variable.woff2"
    f.save(str(out_woff2))
    print(f"  ✓ {out_woff2.name} ({out_woff2.stat().st_size / 1024:.0f}K)")


def autohint(ttf_path: Path) -> bool:
    if not TTFAUTOHINT:
        return False
    tmp = ttf_path.with_suffix(".hinted.ttf")
    result = subprocess.run(
        [
            TTFAUTOHINT,
            "--no-info",
            "--composites",
            "--default-script=latn",
            "--fallback-script=latn",
            "--hinting-range-min=8",
            "--hinting-range-max=72",
            str(ttf_path),
            str(tmp),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False
    shutil.move(str(tmp), str(ttf_path))
    return True


def build_static_instances():
    print(f"\n[2/2] Static instances (4 weights)")
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

    for label, wght in WEIGHT_INSTANCES:
        f = TTFont(str(SOURCE_VF))
        f = instantiateVariableFont(f, {"wght": wght})
        activate_tnum(f)
        full_name = f"{FAMILY} {label}"
        ps_name = f"IncruitSans-{label}"
        clean_names(f, full_name, VERSION, ps_name, label)

        out_ttf = STATIC_DIR / f"IncruitSans-{label}.ttf"
        f.save(str(out_ttf))

        hinted = autohint(out_ttf)

        f2 = TTFont(str(out_ttf))
        f2.flavor = "woff2"
        out_woff2 = STATIC_DIR / f"IncruitSans-{label}.woff2"
        f2.save(str(out_woff2))

        ttf_size = out_ttf.stat().st_size / (1024*1024)
        woff2_size = out_woff2.stat().st_size / 1024
        hint_tag = "✅ hinted" if hinted else "no hinting"
        print(f"  ✓ {label:8s} (wght {wght}) → {ttf_size:.1f}M ttf / {woff2_size:.0f}K woff2  [{hint_tag}]")


def main():
    if not SOURCE_VF.exists():
        print(f"✗ Source VF missing: {SOURCE_VF}", file=sys.stderr)
        return 1

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    print(f"Incruit Sans v{VERSION} production build")
    print(f"  source: {SOURCE_VF.name}")
    print(f"  ttfautohint: {'available' if TTFAUTOHINT else 'NOT available'}")

    build_vf()
    build_static_instances()

    license_src = PROJECT_ROOT / "src" / "pretendard-1.3.9" / "LICENSE.txt"
    if license_src.exists():
        shutil.copy(license_src, OUT_DIR / "OFL.txt")
        shutil.copy(license_src, STATIC_DIR / "OFL.txt")
        print(f"\n  ✓ OFL.txt copied to {OUT_DIR}/ and {STATIC_DIR}/")

    print(f"\n✓ v{VERSION} production build complete")
    print(f"  VF:     {OUT_DIR}/IncruitSans-Variable.{{ttf,woff2}}")
    print(f"  Static: {STATIC_DIR}/IncruitSans-{{Light,Regular,Medium,Bold}}.{{ttf,woff2}}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
