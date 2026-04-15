from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from retrieval.search import SearchService


class RetrievalSearchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        cache_dir = Path(self.temp_dir.name)

        modules = pd.DataFrame(
            [
                {
                    "moduleCode": "CS1010",
                    "title": "Programming Methodology",
                    "faculty": "Computing",
                    "department": "Computer Science",
                    "description_clean": "Learn Python and programming fundamentals.",
                    "module_text": "Programming Methodology. Learn Python and programming fundamentals.",
                    "moduleCredit": 4,
                },
                {
                    "moduleCode": "ACC1701",
                    "title": "Accounting for Decision Makers",
                    "faculty": "Business",
                    "department": "Accounting",
                    "description_clean": "Financial statements and accounting basics.",
                    "module_text": "Accounting for Decision Makers. Financial statements and accounting basics.",
                    "moduleCredit": 4,
                },
            ]
        )
        degree_profiles = pd.DataFrame(
            [
                {
                    "faculty": "Computing",
                    "department": "Computer Science",
                    "profile_text": "Programming software systems algorithms and data.",
                    "word_count": 6,
                    "degree_label": "Computer Science",
                }
            ]
        )
        jobs = pd.DataFrame(
            [
                {
                    "job_id": "job-1",
                    "title": "Software Engineer",
                    "description_clean": "Build APIs with Python and software engineering practices.",
                    "job_text": "Software Engineer. Build APIs with Python and software engineering practices.",
                    "company": "Acme",
                    "categories": ["Information Technology"],
                    "categories_str": "Information Technology",
                    "skills": ["Python", "APIs"],
                    "job_url": "https://example.com/jobs/1",
                },
                {
                    "job_id": "job-2",
                    "title": "Accountant",
                    "description_clean": "Prepare financial statements and reports.",
                    "job_text": "Accountant. Prepare financial statements and reports.",
                    "company": "Beta",
                    "categories": ["Finance"],
                    "categories_str": "Finance",
                    "skills": ["Accounting"],
                    "job_url": "https://example.com/jobs/2",
                },
            ]
        )

        modules.to_parquet(cache_dir / "modules_clean.parquet", index=False)
        degree_profiles.to_parquet(cache_dir / "degree_profiles.parquet", index=False)
        jobs.to_parquet(cache_dir / "jobs_clean.parquet", index=False)

        np.save(cache_dir / "module_embeddings_all-MiniLM-L6-v2.npy", np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32))
        np.save(cache_dir / "degree_embeddings_all-MiniLM-L6-v2.npy", np.array([[1.0, 0.0]], dtype=np.float32))
        np.save(cache_dir / "job_embeddings_all-MiniLM-L6-v2.npy", np.array([[0.9, 0.1], [0.1, 0.9]], dtype=np.float32))
        np.save(cache_dir / "skill_overlap_matrix_job_skill_coverage_v1.npy", np.array([[1.0, 0.0]], dtype=np.float32))

        self.service = SearchService(cache_dir=cache_dir)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_module_code_lookup_returns_jobs(self) -> None:
        response = self.service.find_jobs("cs 1010")
        self.assertEqual(response.matchedEntity.type, "module")
        self.assertEqual(response.results[0].title, "Software Engineer")

    def test_degree_lookup_returns_jobs(self) -> None:
        response = self.service.find_jobs("computer science")
        self.assertEqual(response.matchedEntity.type, "degree")
        self.assertEqual(response.results[0].title, "Software Engineer")

    def test_unknown_degree_returns_suggestions(self) -> None:
        response = self.service.find_jobs("computer scence")
        self.assertTrue(response.warnings)
        self.assertEqual(response.results, [])

    def test_job_query_returns_modules(self) -> None:
        class DummyModel:
            def encode(self, texts, normalize_embeddings=True):
                self.last = texts
                return np.array([[1.0, 0.0]], dtype=np.float32)

        self.service._model = DummyModel()
        response = self.service.find_modules("python software engineer")
        self.assertEqual(response.results[0].moduleCode, "CS1010")

    def test_short_module_query_returns_warning(self) -> None:
        response = self.service.find_modules("AI")
        self.assertTrue(response.warnings)
        self.assertEqual(response.results, [])

    def test_explore_job_query_returns_combined_sections(self) -> None:
        class DummyModel:
            def encode(self, texts, normalize_embeddings=True):
                self.last = texts
                return np.array([[1.0, 0.0]], dtype=np.float32)

        self.service._model = DummyModel()
        response = self.service.explore("python software engineer")
        self.assertEqual(response.intent, "job_query")
        self.assertEqual(response.jobs[0].title, "Software Engineer")
        self.assertEqual(response.modules[0].moduleCode, "CS1010")
        self.assertEqual(response.degrees[0].degreeLabel, "Computer Science")

    def test_loader_rejects_mismatched_degree_embeddings(self) -> None:
        cache_dir = Path(self.temp_dir.name)
        np.save(
            cache_dir / "degree_embeddings_all-MiniLM-L6-v2.npy",
            np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32),
        )

        with self.assertRaisesRegex(
            ValueError,
            "Degree embeddings row count \\(2\\) does not match the metadata row count \\(1\\)",
        ):
            SearchService(cache_dir=cache_dir)


if __name__ == "__main__":
    unittest.main()
