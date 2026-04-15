# Appendix

## Reproducibility Notes

Docs are Markdown, built with MkDocs Material (`mkdocs.yml`). Main code:

| Component                         | Purpose                            |
| --------------------------------- | ---------------------------------- |
| `notebooks/main.ipynb`            | Analysis, evaluation, figures      |
| `retrieval/data.py`               | Text cleaning, corpus construction |
| `retrieval/search.py`             | Deterministic job/module retrieval |
| `scripts/build_chat_index.py`     | Offline artifact builder           |
| `scripts/run_retrieval_server.py` | Demo HTTP API                      |
| `tests/test_retrieval.py`         | Retrieval regression tests         |

Docs: install `requirements-docs.txt`, run `mkdocs serve`. Demo: `.venv/bin/python scripts/build_chat_index.py`, then `.venv/bin/python scripts/run_retrieval_server.py` and `npm run dev` for the UI.

---

## Notes On Interpretation

- Notebook: 15 curated degree proxies; the app is a lighter explorer.
- Degree-to-job scores pool evidence from top modules, not one module alone.
- Offline metrics disagree: hybrid is stronger on pairwise agreement; cluster-routed semantic leads `NDCG@5` and several top-k precisions. The app still uses hybrid for degree lookups for explainability.
