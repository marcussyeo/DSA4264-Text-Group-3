# Appendix

## Reproducibility Notes

The documentation site is written in Markdown and rendered with MkDocs Material through `mkdocs.yml`. The main implementation references are:

| Component                         | Purpose                                                |
| --------------------------------- | ------------------------------------------------------ |
| `notebooks/main.ipynb`            | End-to-end analysis, evaluation, and figure generation |
| `retrieval/data.py`               | Text cleaning and corpus construction utilities        |
| `retrieval/search.py`             | Deterministic retrieval logic for jobs and modules     |
| `scripts/build_chat_index.py`     | Offline artifact builder                               |
| `scripts/run_retrieval_server.py` | HTTP API for the demo app                              |
| `tests/test_retrieval.py`         | Basic regression tests for retrieval behaviour         |

To rebuild the documentation locally, install `requirements-docs.txt` and run `mkdocs serve`. To refresh the demo artifacts, run `.venv/bin/python scripts/build_chat_index.py`, then start the API with `.venv/bin/python scripts/run_retrieval_server.py` and the frontend with `npm run dev`.

## Notes On Interpretation

- The notebook analysis profiles 15 curated degree proxies, while the app is a lighter exploratory interface.
- Degree-to-job scores aggregate evidence from top-matching modules rather than from a single module.
- Offline results split by metric: hybrid leads balanced pairwise agreement, while cluster-routed semantic leads `NDCG@5` and several top-k precision metrics. The app still prioritises the hybrid score for degree lookups because it is easier to explain.
