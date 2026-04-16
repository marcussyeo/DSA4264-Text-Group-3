from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from analysis.embedding import aggregate_top_k_similarity
from analysis.hybrid import build_hybrid_matrix, extract_skills_from_text
from analysis.io import build_paths
from analysis.preprocessing import extract_level, parse_job_file, strip_html


class AnalysisHelpersTests(unittest.TestCase):
    def test_strip_html_normalises_spacing(self) -> None:
        self.assertEqual(strip_html("<p>Hello <b>world</b></p>"), "Hello world")

    def test_extract_level_uses_first_digit(self) -> None:
        self.assertEqual(extract_level("CS1010"), 1)
        self.assertEqual(extract_level("CS5321"), 5)

    def test_parse_job_file_extracts_lists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "job.json"
            path.write_text(
                json.dumps(
                    {
                        "metadata": {"jobPostId": "job-1", "newPostingDate": "2026-01-01"},
                        "title": "Software Engineer",
                        "description": "<p>Build APIs</p>",
                        "skills": [{"skill": "Python"}],
                        "categories": [{"category": "Information Technology"}],
                        "positionLevels": [{"position": "Fresh/entry level"}],
                        "employmentTypes": [{"employmentType": "Full Time"}],
                        "postedCompany": {"name": "Acme"},
                    }
                ),
                encoding="utf-8",
            )
            parsed = parse_job_file(path)
            self.assertIsNotNone(parsed)
            self.assertEqual(parsed["job_id"], "job-1")
            self.assertEqual(parsed["skills"], ["Python"])

    def test_build_paths_discovers_repo(self) -> None:
        paths = build_paths(Path(__file__).resolve())
        self.assertTrue(paths.repo_root.exists())
        self.assertEqual(paths.data_dir.name, "data")

    def test_aggregate_top_k_similarity_handles_module_axis(self) -> None:
        matrix = np.array([[0.1, 0.8], [0.7, 0.2], [0.5, 0.4]], dtype=np.float32)
        result = aggregate_top_k_similarity(matrix, top_k=2)
        np.testing.assert_allclose(result, np.array([0.6, 0.6], dtype=np.float32))

    def test_skill_extraction_and_hybrid_matrix(self) -> None:
        found = extract_skills_from_text("Python data analysis and sql", ["data analysis", "python", "sql"])
        self.assertEqual(found, {"data analysis", "python", "sql"})

        sim = np.array([[0.8, 0.2]], dtype=np.float32)
        skill = np.array([[0.5, 0.0]], dtype=np.float32)
        hybrid = build_hybrid_matrix(sim, skill, alpha=0.7, beta=0.3)
        np.testing.assert_allclose(hybrid, np.array([[0.71, 0.14]], dtype=np.float32))


if __name__ == "__main__":
    unittest.main()
