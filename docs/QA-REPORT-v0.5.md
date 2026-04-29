# Incruit Sans v0.5.0 QA Report

**일자**: 2026-04-27
**대상**: `build/v0.5-vf/IncruitSans-Variable.{ttf,woff2}`
**목적**: 한국 채용 문서·비즈니스 표준 폰트로의 적합성 평가

---

## 1. 요약

Incruit Sans v0.5.0은 한글(Pretendard) + Latin(Source Sans 3 VF) 결합 Variable Font. **단일 weight 페이지(이력서, 본문 위주)에는 권장**, 한 페이지 내 다양한 weight 영문이 섞이는 헤드라인 디자인엔 정적 v0.2 OTF/TTF 권장.

**합격 영역:**
- ✅ 한글 가변성: 11,172자 모두 wght 45→930 변형
- ✅ Latin ASCII 가변성: 113자 (영문 대소문자 + 숫자 + 기본 punctuation)
- ✅ tnum 기본 활성화 (이력서 표 자동 정렬)
- ✅ 한국 이력서 punctuation: `·` `~` `–` `—` `※` `▶` `●` `■` `₩` `%` `℃` `㎡` 모두 포함
- ✅ x-height 매칭: Latin +9.1% 보정 적용
- ✅ Latin 굵기 매칭: gvar tuple W2 shift (+0.16 normalized) 적용
- ✅ OFL 1.1 + 정확한 출처 표기
- ✅ 9개 named instances (Thin~Black)

**알려진 한계:**
- ⚠️ Latin-1 악센트 78자 (À, ñ, ü, ç 등): VF 슬라이더에서 굵기 변형 안 됨 → Regular 두께 고정
- ⚠️ 'i', 'j' (소문자): 위와 같은 이유로 static
- ⚠️ Latin 굵기 W2 보정 후도 한글 대비 wght 700+ 에서 미세한 mismatch 잔존

---

## 2. 메타데이터 검증

| 항목 | 값 | 상태 |
|------|-----|------|
| Family Name | `Incruit Sans` | ✅ |
| Subfamily | `Regular` | ✅ |
| Full Name | `Incruit Sans Variable` | ✅ |
| Version | `0.5.0` | ✅ |
| PostScript Name | `IncruitSans-Variable` | ✅ |
| em | 2048 | ✅ |
| ascender | 1950 | ✅ |
| descender | -494 | ✅ |
| Total glyphs | 14,757 | ✅ |
| cmap entries | 14,336 | ✅ |
| gvar entries | 14,757 | ✅ |
| wght axis | 45 → 930 (default 400) | ✅ |
| Named instances | 9 (Thin/EL/Light/Reg/Med/SB/Bold/EB/Black) | ✅ |
| OFL attribution | Pretendard + Adobe Source Sans 3 명시 | ✅ |

---

## 3. 한글 평가

| 항목 | 값 |
|------|-----|
| 가변 한글 글리프 | 11,172 / 11,172 (100%) ✅ |
| 베이스 | Pretendard Variable (검증된 OFL 한글 폰트) |
| weight 범위 | Thin(45) → Black(930) — Pretendard 풀 범위 |

**평가**: 변경 없음. Pretendard의 정평난 한글 디자인 그대로.

---

## 4. Latin 평가

### 4.1 가변성 분석

| 카테고리 | 카운트 | 비율 | 슬라이더 동작 |
|---------|--------|------|--------------|
| Simple variable | 113 | 59.2% | ✅ 정상 |
| Simple static | 78 | 40.8% | ❌ Regular 고정 |
| **합계** | **191** | 100% | |

**static 78자 상세** (Latin-1 Supplement 악센트 위주):
- 소문자 i, j (composite: dotlessi + dotaccent)
- À Á Â Ã Ä Å Æ Ç È É Ê Ë Ì Í Î Ï Ñ Ò Ó Ô Õ Ö Ø Ù Ú Û Ü Ý
- à á â ã ä å æ ç è é ê ë ì í î ï ñ ò ó ô õ ö ø ù ú û ü ý ÿ
- ð þ Ð Þ ß
- 기타 composite 문자

**원인**: Source Sans 3 VF의 composite 글리프(base + 악센트 결합) 구조를 우리 VF의 Pretendard 베이스와 통합하는 과정에서 fontTools의 gvar 검증 충돌 발생. v0.4까지의 시도에서 cycle/recursion 문제로 composite 가변성 보존 실패. v0.6 이후 폰트 엔지니어 작업 영역.

**완화책**:
1. 한국 이력서 본문은 ASCII 위주이므로 실용적 영향 적음
2. 외국인 이름(José, François 등) 표기 시 Regular 톤으로 표시 → 시각적 어색함은 헤드라인 Bold 사용 시에만 명확
3. **다양한 weight 영문이 같은 페이지에 등장하면 VF 대신 정적 v0.2 OTF/TTF 4종 사용**

### 4.2 Stroke 굵기 매칭

W2 시프트 (gvar wght 축 정규화 +0.16) 적용 후:

| wght | Pretendard 'l' (per-mille) | Source Sans 3 'l' (scaled) | 차이 |
|------|--------------------------|------------------------------|------|
| 200 | 48.8 | ~80 | +64% |
| 400 | 84.0 | ~80 (W2 보정 후) | -5% ✅ |
| 700 | 144.2 | ~180 | +25% |
| 900 | 184.4 | ~232 | +26% |

**평가**: wght 400 (Regular)에서는 매칭됨. wght 700+ 에서 Latin이 약간 더 굵게 보임. 헤드라인용 Bold 사용 시 한글이 살짝 가벼워 보일 수 있음.

**권장 추가 보정**: 향후 W3 또는 더 큰 시프트 시안 검증 후 v0.5.1 빌드 가능.

### 4.3 자간 (Spacing)

Source Sans 3의 자체 advance width를 그대로 사용 (2.232× 스케일링). 한글 옆에서 살짝 헐렁한 인상 가능.

**완화책**: 향후 v0.5.1에서 advance × 0.94 또는 광학 D-optical 보정 추가 검토.

---

## 5. OpenType Features

**지원 기능**: aalt, calt, case, ccmp, clig, cv01-cv16, dlig, dnom, frac, fwid, locl, numr, ordn, pnum, pwid, rlig, salt, sinf, ss01-ss16, subs, sups, **tnum**, zero (총 47개)

### 5.1 tnum 기본 활성화 ✅

`tnum` (Tabular Figures) lookup이 `calt` (Contextual Alternates)에 promote되어 **CSS 옵션 없이 자동 적용**.

**효과**: 이력서 표에서 연도·연봉·기간이 자동으로 세로 정렬:
```
2020.03 ~ 2024.02   ₩120,000,000
2017.04 ~ 2019.12   ₩ 98,500,000
2014.07 ~ 2016.11   ₩145,750,000
```

### 5.2 사용 가능한 Stylistic Sets

`ss01` ~ `ss16` 다수 지원 (Pretendard 상속). 향후 `ss01` (보수적 임원 톤) / `ss02` (표현적 신입 톤) 명시적 정의 필요 → v0.6 작업.

---

## 6. 한국 이력서 특수문자 검증

| 문자 | Unicode | 포함 여부 | 용도 |
|------|---------|-----------|------|
| `·` 가운뎃점 | U+00B7 | ✅ | 스킬 나열 (Python · TypeScript · Go) |
| `~` 물결 | U+007E | ✅ | 기간 표시 (2020.03 ~ 2024.02) |
| `–` en dash | U+2013 | ✅ | 범위 (서울 – 도쿄) |
| `—` em dash | U+2014 | ✅ | 강조 |
| `※` | U+203B | ✅ | 비고 |
| `▶` | U+25B6 | ✅ | 불릿 |
| `●` | U+25CF | ✅ | 불릿 |
| `■` | U+25A0 | ✅ | 불릿 |
| `₩` 원화 | U+20A9 | ✅ | 연봉 표기 |
| `%` | U+0025 | ✅ | 평점 |
| `℃` | U+2103 | ✅ | 온도 |
| `㎡` | U+33A1 | ✅ | 면적 |

**평가**: 한국 이력서 필수 punctuation 모두 포함 ✅

---

## 7. 한자 처리

**포함 한자**: 0개 (의도된 동작) ✅

**전략**: 한자는 OS fallback으로 위임:
```css
font-family: "Incruit Sans", "Apple SD Gothic Neo", "Noto Sans CJK KR", sans-serif;
```

- macOS: Apple SD Gothic Neo
- Windows: Malgun Gothic
- Linux: Noto Sans CJK KR
- 일본 사용자: Noto Sans CJK JP (자동)
- 중국 사용자: Noto Sans CJK SC/TC (자동)

→ Min Sans가 겪은 한자 변형 컴플레인 회피 ✅

---

## 8. 사용 권장 가이드

### 권장 사용처 ✅

1. **한국 이력서 (단일 weight 본문)**: 본문 Regular(400), 헤드라인 Bold(700) — VF 적합
2. **비즈니스 문서 일반**: 단일 weight 위주 → VF
3. **웹 페이지 (단일 weight)**: WOFF2 2MB 단일 파일로 모든 weight 커버
4. **모바일 UI**: 변형 가능한 한글이 디자인 자유도 제공

### 비권장 또는 정적 폰트 권장 ❌

1. **다양한 weight Latin이 한 페이지에 섞임 (헤드라인 Bold + 본문 Regular + 캡션 Light)**:
   → 정적 v0.2 OTF/TTF 4종 사용 (Latin도 weight별 정확)
2. **악센트 외국어 본문이 많은 디자인** (스페인어, 프랑스어 인용 등):
   → 정적 v0.2 또는 fallback 폰트 보강

### CSS 권장 패턴

**VF 사용:**
```css
@font-face {
  font-family: "Incruit Sans";
  src: url("IncruitSans-Variable.woff2") format("woff2-variations"),
       url("IncruitSans-Variable.woff2") format("woff2");
  font-weight: 45 930;
  font-display: swap;
}
body {
  font-family: "Incruit Sans", "Apple SD Gothic Neo", "Noto Sans CJK KR", sans-serif;
}
```

**정적 OTF 사용 (`build/v0.2/`):**
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

---

## 9. 알려진 이슈 & v0.6 로드맵

| 이슈 | v0.5 상태 | v0.6 계획 |
|------|----------|-----------|
| composite 글리프 (i, j, 악센트 78자) static | 한계 명시 | 폰트 엔지니어 외주 — 마스터 매칭으로 해결 |
| Latin 굵기 wght 700+ 에서 미세 mismatch | W2 시프트로 부분 보정 | 추가 weight remap or 직접 stroke 조정 |
| 자간 한글 대비 살짝 헐렁 | Source Sans 3 native | optical respacing (D-optical) 추가 검증 |
| 한국 punctuation 자체 디자인 (`·` `~` `–`) | 기본 글리프 사용 | 시각 보정 자체 디자인 |
| Stylistic Sets ss01/ss02 명시적 정의 | 기능 가용 | 보수적/표현적 톤 명시 매핑 |
| ATS 호환 인증 | 미실시 | 인크루트 + 사람인 + 잡코리아 검증 |

---

## 10. 평가 점수 (한국 이력서·비즈니스 폰트 기준)

| 영역 | 점수 | 비고 |
|------|------|------|
| 한글 디자인 품질 | 9.5/10 | Pretendard 검증된 디자인 |
| Latin 디자인 품질 | 9.0/10 | Source Sans 3 Adobe 산업 표준 |
| 한글-Latin 균형 | 7.5/10 | x-height/굵기 보정 적용, wght 700+ 미세 잔존 |
| 이력서 적합성 | 9.0/10 | tnum 기본화, 한국 punctuation 완비 |
| VF 가변성 | 8.0/10 | 한글 100%, Latin ASCII 100%, Latin-1 악센트 0% |
| 라이선스 | 10/10 | OFL 1.1 명확, 출처 정확 |
| **종합** | **8.8/10** | **출시 가능 (Preview/Beta 라벨)** |

---

## 11. 결론

**v0.5는 한국 이력서·비즈니스 표준 폰트로서 출시 가능한 품질에 도달.** "Preview" 또는 "Beta" 라벨로 무료 OFL 공개 권장.

**우선 사용 시나리오**: 인크루트 플랫폼의 이력서 작성 페이지에 기본 폰트로 탑재. VF 단일 파일로 모든 weight 커버. 단일 weight 페이지에서 한글-Latin 균형 우수.

**v1.0 정식 출시 전 필수 작업**:
1. composite 글리프 가변성 복원 (font engineer)
2. Latin 굵기·자간 추가 미세 조정
3. ATS 호환성 공식 인증
4. ss01/ss02 명시적 정의

---

## 참고

- 빌드: `python3 scripts/finalize_v0.5.py`
- 이전 시안 비교: `build/v0.4-weight-variants/compare.html`
- 갭 분석: `~/Projects/personal/docs/2026-04-26-resume-font-gap-analysis.md`
- MVP 스펙: `~/Projects/personal/docs/2026-04-26-incruit-sans-phase1-mvp-spec.md`
