# Technical Report

## Auditable Curriculum-Job Alignment for Public Decision-Making

This report documents a retrieval-based framework for assessing how closely university curricula align with current labour-market demand. The aim is practical rather than punitive: an agency such as MOE needs an auditable way to detect where programmes appear aligned, where gaps may be emerging, and where deeper curriculum review may be warranted. The framework is therefore designed to support judgement, not replace it.

The project combines NUS module descriptions with MyCareersFuture job advertisements, converts both into comparable text representations, and evaluates lexical, semantic, skill-based, hybrid, and cluster-routed ranking methods on an internal benchmark spanning 15 degree proxies. The repo retains 616 provenance-rich labelled pairs, while the final notebook evaluation runs on 256,350 matched pairs in the current corpus. No single method dominates every metric: hybrid semantic + skill is strongest on balanced pairwise agreement and `Precision@3`, while cluster-routed semantic leads `NDCG@5`, `Precision@1`, and `Precision@5`.
