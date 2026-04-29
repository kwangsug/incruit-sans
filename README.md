# Incruit Sans

**한국 이력서 표준 글꼴 OFL 폰트**

A Korean font optimized for resumes, CVs, and recruitment documents. Based on Pretendard with Incruit-specific tuning.

## v1.0.0 (2026-04-29)

세션 중 외부 Latin 결합(Source Sans 3, Open Sans, Roboto Flex, Min Sans) 4종 모두 평가한 결과, **Pretendard 자체 디자인이 한글-Latin 균형 가장 자연스러움** 결론. v1.0은 Pretendard 통째 리브랜드 + 인크루트 채용 문서 특화 튜닝.

### 차별화

1. **`tnum` (Tabular Figures) 기본 활성화** — CSS 옵션 없이 이력서 표가 자동 정렬
2. **한국 이력서 punctuation 완비** — `·` `~` `–` `—` `※` `▶` `●` `■` `₩` `%` `℃` `㎡`
3. **9pt 인쇄 최적 hinting** — ttfautohint 적용된 정적 TTF
4. **한자는 OS fallback** — 본고딕 / Apple SD / Noto CJK (Min Sans의 한자 변형 이슈 회피)
5. **OFL 1.1** — 무료 자유 배포

### 다운로드

**Variable Font** (web/UI 권장) — `build/v1.0/`
- `IncruitSans-Variable.ttf` (6.4M) + `.woff2` (2.0M)
- wght 45→930, 9 instances

**Static OTF** — `build/v1.0/static/`
- `IncruitSans-{Light,Regular,Medium,Bold}.otf` + `.woff2`

**Static TTF** (인쇄 최적, hinting 적용) — `build/v1.0/static/ttf/`
- `IncruitSans-{Light,Regular,Medium,Bold}.ttf` + `.woff2`

## 사용

**CSS (Variable Font):**
```css
@font-face {
  font-family: "Incruit Sans";
  src: url("IncruitSans-Variable.woff2") format("woff2-variations");
  font-weight: 45 930;
  font-display: swap;
}

body {
  font-family: "Incruit Sans", "Apple SD Gothic Neo", "Noto Sans CJK KR", sans-serif;
}
```

**CSS (Static):**
```css
@font-face {
  font-family: "Incruit Sans";
  src: url("IncruitSans-Regular.woff2") format("woff2");
  font-weight: 400;
}
@font-face {
  font-family: "Incruit Sans";
  src: url("IncruitSans-Bold.woff2") format("woff2");
  font-weight: 700;
}
```

**시스템 설치:**
```bash
cp build/v1.0/static/*.otf ~/Library/Fonts/        # macOS
cp build/v1.0/IncruitSans-Variable.ttf ~/Library/Fonts/
```

## 빌드

```bash
python3 scripts/build_v1.0_pretendard_only.py
```

소스: `src/pretendard-1.3.9/` (download Pretendard v1.3.9 release first)

## 라이선스

**SIL Open Font License 1.1**

이 폰트는 [Pretendard](https://github.com/orioncactus/pretendard) (Copyright 2021 Kil Hyung-jin)을 기반으로 제작되었습니다. Pretendard 역시 OFL 1.1로 배포됩니다.

전문은 `OFL.txt` 또는 `build/v1.0/OFL.txt` 참조.

## 로드맵

- **v1.0** (2026-04-29) — Pretendard 리브랜드 + tnum 기본화 + ttfautohint ✅
- **v1.1+** — 한국 이력서 punctuation 자체 시각 보정, Stylistic Sets ss01/ss02, ATS 호환 인증 (외주 폰트 엔지니어 영역)

폰트 엔지니어 섭외 자료: [`docs/v0.2-font-engineer-rfp.md`](docs/v0.2-font-engineer-rfp.md), [`docs/recruitment-post.md`](docs/recruitment-post.md)

## 참고

- Pretendard: https://github.com/orioncactus/pretendard
- SIL Open Font License: https://openfontlicense.org
