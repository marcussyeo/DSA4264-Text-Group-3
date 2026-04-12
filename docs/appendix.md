# Appendix

## Reproducibility Notes

The documentation site is written in Markdown and rendered with MkDocs Material through `mkdocs.yml`. The main implementation references are:

| Component | Purpose |
| --- | --- |
| `notebooks/main.ipynb` | End-to-end analysis, evaluation, and figure generation |
| `retrieval/data.py` | Text cleaning and corpus construction utilities |
| `retrieval/search.py` | Deterministic retrieval logic for jobs and modules |
| `scripts/build_chat_index.py` | Offline artifact builder |
| `scripts/run_retrieval_server.py` | HTTP API for the demo app |
| `tests/test_retrieval.py` | Basic regression tests for retrieval behaviour |

To rebuild the documentation locally, install `requirements-docs.txt` and run `mkdocs serve`. To refresh the demo artifacts, run `.venv/bin/python scripts/build_chat_index.py`, then start the API with `.venv/bin/python scripts/run_retrieval_server.py` and the frontend with `npm run dev`.

## Notes On Interpretation

Three implementation choices matter when interpreting results. First, the notebook analysis uses curated degree baskets for five programmes, while the app is a lighter exploratory interface. Second, degree-to-job scores are aggregated from top-matching modules rather than a single module. Third, the strongest offline method is cluster-routed semantic retrieval, but the app prioritises the hybrid score for degree lookups because it is easier to explain.
