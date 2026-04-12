# Technical Report

## Auditable Curriculum-Job Alignment for Public Decision-Making

This report documents a retrieval-based framework for assessing how closely university curricula align with current labour-market demand. The aim is practical rather than punitive: an agency such as MOE needs an auditable way to detect where programmes appear aligned, where gaps may be emerging, and where deeper curriculum review may be warranted. The framework is therefore designed to support judgement, not replace it.

The project combines NUS module descriptions with MyCareersFuture job advertisements, converts both into comparable text representations, and evaluates lexical, semantic, skill-based, hybrid, and cluster-routed ranking methods on a shared internal gold set. Cluster-routed semantic retrieval performs best overall, while the hybrid semantic-plus-skill score is nearly as strong and easier to explain because it separates semantic similarity from explicit skill coverage.

## Report Structure

| Section | What it covers |
| --- | --- |
| Project Overview | Problem framing, stakeholders, data sources, and scope |
| Methodology | Data cleaning, degree-profile construction, scoring methods, and execution design |
| Results | Quantitative comparison, qualitative examples, and policy interpretation |
| Appendix | Reproducibility notes, repository map, and implementation references |
