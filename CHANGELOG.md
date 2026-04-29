# Changelog

## [1.0.0] — 2026-04-28

### First production candidate release

**Combined**
- Hangul: Pretendard Variable (Kil Hyung-jin, OFL 1.1)
- Latin: Roboto Flex (Christian Robertson, David Berlow / Google, OFL 1.1)
- Latin gvar delta × 0.70 reduction (visual review optimum for Hangul-Latin balance)
- em 2048 (no scaling, hinting preserved)

**Features**
- 변형 가능 Latin: 128 글리프 (Basic Latin + Latin-1 Supplement)
- `tnum` (Tabular Figures) **기본 활성화** — 이력서 표 자동 정렬
- 한국 이력서 punctuation 완비: `·` `~` `–` `—` `※` `▶` `●` `■` `₩` `%` `℃` `㎡`
- Stroke 매칭: wght 700 +0.7%, wght 900 -1.5% (거의 완벽)
- ttfautohint 적용 (4 static TTF, 9pt 인쇄 최적화)

**Outputs**
- Variable Font: `IncruitSans-Variable.ttf` (6.4M) + `.woff2` (2.0M)
- Static: Light(300) / Regular(400) / Medium(500) / Bold(700) — TTF + WOFF2

**Known limitations (v2.0 roadmap)**
- Composite Latin 60자 (i, j, À-ÿ): VF에서 static (Regular 고정)
- 한국 punctuation 자체 시각 디자인: 미적용 (Pretendard 기본 사용)
- ATS 호환 공식 인증: 미실시
