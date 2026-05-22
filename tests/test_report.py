import os
import tempfile
import pytest
import report


class TestReport:
    def test_generate_txt(self):
        results = {
            "Dev": {
                "PORTAL": [
                    {"title": "Job", "company": "Co", "location": "CL",
                     "date": "Hoy", "url": "https://example.com/job",
                     "portal": "PORTAL", "best_effort": False}
                ]
            }
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = report.generate(results, tmpdir)
            assert os.path.exists(path)
            content = open(path, encoding="utf-8").read()
            assert "Job" in content
            assert "Co" in content

    def test_generate_empty(self):
        results = {"Dev": {"PORTAL": []}}
        with tempfile.TemporaryDirectory() as tmpdir:
            path = report.generate(results, tmpdir)
            assert os.path.exists(path)
            content = open(path, encoding="utf-8").read()
            assert "Sin resultados" in content
