# Project Overview

## Policy Problem

This project addresses a public-policy question: how can a ministry or university evaluate whether curriculum content is keeping pace with labour-market demand without relying on anecdote, media narratives, or one-off employer surveys? In practice, curriculum review is slow, while job demand changes quickly. A scalable text-analytic framework can therefore act as an early warning system by surfacing where alignment appears strong, mixed, or in need of human review.

Curriculum relevance is multi-dimensional and should not be reduced to a single score. Some programmes intentionally serve broad civic, scientific, or foundational goals that do not map neatly to short-term job ads, so the outputs should be read as structured evidence about present labour-market alignment rather than a final statement about programme quality.

## Stakeholders And Intended Use

The main stakeholder is MOE, which needs evidence that is scalable, explainable, and robust enough for policy discussion. Universities are a second stakeholder because they need interpretable evidence when reviewing core modules, electives, and common curriculum requirements. Students and employers also benefit indirectly: students gain a clearer picture of which learning pathways connect to job families, while employers gain a better articulation of where university training already overlaps with industry needs.

The design choices in this report are guided by stakeholder needs. We prioritise transparent retrieval methods over opaque end-to-end prediction, preserve textual evidence for every match, and report limitations explicitly so that the framework supports deliberation rather than replacing it.

## Data Sources

The analysis combines curriculum text with labour-market text.

| Source | Role in framework | Scale used in report |
| --- | --- | --- |
| NUSMods API via `data/modules.csv` | Supplies module titles, descriptions, faculty, and department metadata | 7,014 raw modules; 4,032 undergraduate modules with sufficiently detailed descriptions after filtering |
| MyCareersFuture JSON postings in `data/MyCareersFutureData/` | Supplies job titles, descriptions, structured skills, and category labels | 22,720 raw postings collected from 25 Jan 2026 to 31 Jan 2026 |

For the main case study, we do not compare all departments at once. Instead, we build 15 curated degree proxies spanning professional, technical, and humanities domains, including Accounting, Architecture, Business Administration, Computer Science, Data Science and Analytics, Pharmacy, Psychology, and Southeast Asian Studies. Most proxies contain 23 modules, with Accounting using 24. This keeps the comparison policy-relevant while ensuring enough textual coverage to build meaningful degree profiles.

## Scope And Boundaries

The report deliberately evaluates alignment, not graduate outcomes. A job ad reflects employer demand language, not actual hiring success, wages, job quality, or long-term career mobility. Likewise, module descriptions are imperfect summaries of what is taught in class. The framework therefore measures textual alignment between advertised demand and documented curriculum content.

The study also uses a one-week job snapshot. This is acceptable for a proof-of-concept because the goal is to test whether the methodology is credible and reproducible, but it means the results should be read as a market snapshot rather than a permanent truth. If policy users were to adopt the framework, the correct next step would be repeated runs over time so that sudden sectoral fluctuations do not drive curriculum conclusions.
