import pytest
from scrapers.base import clean_url, MODALITY_MAP, check_connectivity


class TestCleanUrl:
    def test_removes_tracking_params(self):
        url = "https://example.com/page?utm_source=twitter&q=python&e=123"
        result = clean_url(url)
        assert "utm_source" not in result
        assert "e=" not in result
        assert "q=python" in result

    def test_no_params(self):
        url = "https://example.com/jobs"
        assert clean_url(url) == url

    def test_empty_string(self):
        assert clean_url("") == ""


class TestModalityMap:
    def test_remoto(self):
        assert MODALITY_MAP["remoto"] == "remoto"

    def test_hibrido_accent(self):
        assert MODALITY_MAP["híbrido"] == "hibrido"

    def test_cualquiera(self):
        assert MODALITY_MAP["cualquiera"] == ""


class TestConnectivity:
    def test_connectivity_check(self):
        result = check_connectivity()
        assert isinstance(result, bool)
