# Font Engineer Wanted — Incruit Sans Project

> **Help us build Korea's first font designed for resumes. Open-source (OFL 1.1).**

---

## About

**Incruit** (est. 1998) is a first-generation Korean recruitment platform. After 27 years of processing tens of millions of resumes, we asked one simple question:

**"Why is there no font designed specifically for Korean resumes?"**

Pretendard fits modern UI. Wanted Sans is a recruiter brand font. But **no font is designed for the resume itself** — the artifact at the heart of every job search. Incruit is making the first one, and releasing it under SIL OFL 1.1.

**Incruit Sans differentiation:**
1. `tnum` enabled by default — resume tables auto-align without CSS opt-in
2. Korean resume punctuation visual tuning (`·` `~` `–` `※`)
3. 9pt A4 print legibility certification
4. ATS parsing compatibility certification (Incruit · Saramin · Jobkorea)
5. Stylistic Sets for entry-level (expressive) / executive (conservative) tone

v0.1 shipped (Pretendard rebrand + tnum default). Now we need a font engineer for **v0.2: replace Latin glyphs with Source Sans 3 (Adobe)**.

---

## What You'll Build

### Core Work

**Source Sans 3 (em 1000) → Pretendard (em 2048) Latin glyph merge**

- Scope: Basic Latin + Latin-1 Supplement + Latin Extended-A + selected punctuation/currency (~350 glyphs)
- Em-size normalization (× 2.048 scaling)
- Preserve Pretendard's Hangul, vertical metrics, and GSUB/GPOS structure
- Integrate Source Sans 3 GPOS kerning
- Re-hint OTF (CFF) for 9pt print legibility

### Deliverables

- `IncruitSans-{Light,Regular,Medium,Bold}.otf` × 4 + WOFF2
- `scripts/build_v0.2.py` — reproducible build automation
- 9pt print verification report (5× A4 samples)
- ATS parsing compatibility test report
- Handoff documentation for v0.3 work

---

## Who You Are

### Required

- **Deep OpenType / CFF knowledge** — direct manipulation of name table, cmap, GSUB/GPOS, CFF charstrings
- **Proficient with fontTools (Python) or FontForge / Glyphs / RoboFont**
- **Track record of merging fonts with different em sizes** (glyph scaling + metric reconciliation)
- **Hangul font work experience** — contributed to or forked Pretendard, Source Han Sans, Spoqa Han Sans, SUIT, etc.

### Preferred

- ✨ Pretendard repo contributor
- ✨ Adobe Source family or Google Noto contributor
- ✨ Background at Sandoll Communication, Yoondesign, or AG Typography
- ✨ ATS / PDF embedding compatibility debugging experience
- ✨ Variable Font construction experience (additional contracts at v1.0)

### Not a Fit

- Visual designer in Illustrator only, no font engineering
- TrueType only, no CFF experience
- No OFL licensing experience

---

## Schedule · Compensation

| Item | Detail |
|------|--------|
| **Engagement** | Project-based contract (sole proprietor or company) |
| **Duration** | 4–6 weeks (W1 kickoff → W6 final delivery) |
| **Fee** | **KRW 8M – 15M** (negotiable based on experience) |
| **Payment** | 30% on contract / 40% at W3 / 30% on acceptance |
| **Location** | Fully remote (occasional meetings at Incruit HQ in Seoul) |

### Follow-on Work (Long-term partnership for the right person)

- v0.3: Korean punctuation custom design (3 weeks, KRW 5M)
- v0.4: Stylistic Sets ss01/ss02 (3 weeks, KRW 5M)
- v1.0: Variable Font + 9pt print cert + ATS cert (6 weeks, KRW 15M)
- **incruit-icon**: Variable Icon Font separate project (KRW 15M–25M)

→ KRW 50M+ over 6 months possible

---

## What You'll Get

1. **Designer credit on Korea's resume font standard** — name permanently recorded in OFL license
2. **Adobe + Pretendard dual-fork integration record** — top-tier portfolio item
3. **Incruit platform dogfooding** — your work ships as the default font in Incruit's resume templates
4. **First-right-of-refusal on incruit-icon project**

---

## How to Apply

### Submit

1. **Resume + font portfolio**
   - GitHub repo links
   - 1–2 fonts you've worked on (downloadable OTF/TTF)
2. **Project quote**
   - Total fee
   - Schedule with W1–W6 milestones
   - Earliest start date
3. **Brief intro** (why you're a fit, max 5 sentences)

### Send to

- **Email**: starkid@yonsei.ac.kr
- **Recipient**: Lee Kwang Seok (Chairman, Incruit · AX Office)
- **Reply**: Within **1 week** of submission

### Questions

For technical details, please email. 30-min pre-call available before applying.

---

## Reference Materials (Shared with Applicants)

We share full materials with serious applicants:
- Incruit Sans v0.1 build scripts + outputs
- v0.2 PoC code (191 Latin glyph swap verified working)
- Technical spec + gap analysis + full RFP
- 8 acceptance criteria details

---

## Deadline

**Open until filled** — closing as soon as the right person is identified.

---

> A font engineer's work is etched into millions of resumes every year.<br>
> Want to build Korea's first resume font with us?

—  **Lee Kwang Seok** (Chairman, Incruit Corp.)
