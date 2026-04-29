# Changelog

## [1.0.0] — 2026-04-29 (revised)

### First production release — Pretendard 단순 리브랜드

**Decision rationale**
세션 중 Source Sans 3, Open Sans, Roboto Flex, Min Sans Latin 결합을 모두 평가한 결과, **Pretendard 자체 디자인이 한글-Latin 균형 가장 자연스러움**. 외부 Latin 결합 시 stroke·자간 미스매치 또는 composite 글리프 가변성 손실이 항상 발생.

**Sources (all OFL 1.1)**
- Hangul + Latin: Pretendard Variable & Static (Copyright 2021 Kil Hyung-jin)

**v1.0 modifications over Pretendard**
- Family rebrand: "Pretendard" → "Incruit Sans"
- `tnum` (Tabular Figures) **기본 활성화** (calt에 promote) — 이력서 표 자동 정렬
- 한국 이력서 punctuation 완비 (Pretendard 그대로 활용)
- 메타데이터: name table 17개 항목 재작성, 출처 명시

**Outputs**
- Variable Font: `IncruitSans-Variable.{ttf,woff2}` (wght 45→930, 9 instances)
- Static OTF: `static/IncruitSans-{Light,Regular,Medium,Bold}.{otf,woff2}`
- Static TTF (hinted, 9pt 인쇄 최적): `static/ttf/IncruitSans-{...}.{ttf,woff2}` — ttfautohint 적용

**Roadmap (v2.0+)**
- 한국 이력서 punctuation 자체 시각 보정 (`·` `~` `–` `※`)
- Stylistic Sets ss01/ss02 명시적 정의 (보수적 임원 / 표현적 신입 톤)
- ATS 호환 공식 인증 (인크루트 + 사람인 + 잡코리아)
- 외주 폰트 엔지니어 영역
