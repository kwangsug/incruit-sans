# Incruit Sans

**한국 채용 문서를 위한 첫 번째 표준 폰트**

A Korean + Latin font optimized for resumes, CVs, and recruitment documents.

## 최신 버전: v0.2.0 (2026-04-27)

**Source Sans 3 (Adobe) Latin 글리프 병합 + x-height 매칭 1.09× 보정.**

- 한글: Pretendard (검증된 모던 한글)
- Latin: **Source Sans 3 (Adobe / Paul D. Hunt)** — 전문 문서 톤, 본고딕과 같은 Adobe 가족
- 한자: 미포함 → OS fallback 위임
- 라이선스: **SIL OFL 1.1**

### 다운로드

**Static OTF** (Source Sans 3 Latin 적용) — `build/v0.2/`
- `IncruitSans-{Light,Regular,Medium,Bold}.otf` + WOFF2

**Static TTF** (hinting 적용, 9pt 인쇄 최적화) — `build/v0.2-ttf/`
- `IncruitSans-{Light,Regular,Medium,Bold}.ttf` + WOFF2
- ttfautohint로 hint 명령 추가 (prep/fpgm/cvt 테이블) → Windows·인쇄에서 또렷
- WOFF2 ~1.6~1.8MB / weight (hinting 포함)

**Variable Font** — `build/v0.2-vf/`
- `IncruitSans-Variable.ttf` (6.4M) + WOFF2 (2.0M)
- wght axis: 45 → 930 (9 instances: Thin / EL / Light / Reg / Med / SB / Bold / EB / Black)
- ⚠️ VF의 Latin은 Pretendard 그대로 (Source Sans 3 Latin 병합은 v0.3 작업)
- 데모: `build/v0.2-vf/test.html` (slider로 weight 조절)

## 사용

**CSS:**
```css
@font-face {
  font-family: "Incruit Sans";
  src: url("IncruitSans-Regular.woff2") format("woff2");
  font-weight: 400;
  font-display: swap;
}

body {
  font-family: "Incruit Sans", "Apple SD Gothic Neo", "Noto Sans CJK KR", sans-serif;
}
```

**테스트 페이지:** `build/v0.2/test.html`

## 차별화

1. **`tnum` (Tabular Figures) 기본 활성화** — CSS 옵션 없이 이력서 표가 자동 정렬됨
2. **한글 + Latin 전용 채용 문서 폰트** — 한자는 OS fallback (본고딕/Apple SD/Noto CJK) 위임
3. **Adobe + Pretendard 듀얼 베이스** — 본고딕 fallback 시 메트릭 매끄러움
4. **x-height 측정 기반 정합** — 한글-Latin 시각적 균형 (Latin +9.11% 보정)
5. **OFL 1.1** — 무료 자유 배포

## 빌드

```bash
python3 scripts/build_v0.2.py
```

빌드 결과는 `build/v0.2/`에 출력.

## 라이선스

**SIL Open Font License 1.1**

이 폰트는 다음 두 OFL 1.1 폰트를 기반으로 제작되었습니다:
- [Pretendard](https://github.com/orioncactus/pretendard) (Copyright 2021 Kil Hyung-jin) — Hangul glyphs
- [Source Sans 3](https://github.com/adobe-fonts/source-sans) (Copyright 2010-2020 Adobe / Paul D. Hunt) — Latin glyphs

전문은 `build/v0.2/OFL.txt` 참조.

## 로드맵

- **v0.1** (2026-04-26) — Pretendard 리브랜드 + tnum 기본화 ✅
- **v0.2** (2026-04-27) — Source Sans 3 Latin 병합 + x-height 매칭 ✅
- **v0.3** — 한국 이력서 punctuation 시각 보정 (`·` `~` `–` `※` `▶` `●` `■`)
- **v0.4** — Stylistic Sets `ss01` (보수적·임원) / `ss02` (표현적·신입)
- **v0.5** — ATS 호환 인증 (인크루트 + 사람인 + 잡코리아)
- **v1.0** — 9pt 인쇄 가독성 인증 + Variable Font + 정식 출시

상세 스펙: [`docs/recruitment-post.md`](docs/recruitment-post.md), [`docs/v0.2-font-engineer-rfp.md`](docs/v0.2-font-engineer-rfp.md)

## 디렉토리

```
incruit-sans/
├── README.md
├── src/                            # 소스 폰트 (Pretendard, Source Sans 3)
├── scripts/
│   ├── build_v0.1.py               # v0.1 빌드 (Pretendard 리브랜드)
│   ├── build_v0.2_poc.py           # v0.2 PoC (단일 weight)
│   ├── build_v0.2_variants.py      # 스케일 시안 4종 (A/B/C/D)
│   └── build_v0.2.py               # v0.2 최종 빌드 (4 weight)
├── build/
│   ├── v0.1/                       # v0.1 산출물
│   ├── v0.2-poc/                   # v0.2 단일 weight 검증
│   ├── v0.2-variants/              # 스케일 시안 비교
│   └── v0.2/                       # v0.2 최종 산출물 ⭐
└── docs/
    ├── v0.2-font-engineer-rfp.md   # 엔지니어 섭외 RFP (B2B)
    ├── recruitment-post.md         # 채용 공고 (한)
    └── recruitment-post-en.md      # 채용 공고 (영)
```

## 참고

- Pretendard: https://github.com/orioncactus/pretendard
- Source Sans 3: https://github.com/adobe-fonts/source-sans
- SIL Open Font License: https://openfontlicense.org
