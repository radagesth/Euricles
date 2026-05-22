import pytest
from scrapers.linkedin import LinkedInScraper


class TestLinkedInScraper:
    def test_portal_name(self):
        s = LinkedInScraper()
        assert s.portal_name == "LINKEDIN"

    def test_best_effort(self):
        s = LinkedInScraper()
        assert s.best_effort is True

    def test_modality_to_param(self):
        s = LinkedInScraper()
        assert s._modality_to_param("remoto") == "2"
        assert s._modality_to_param("presencial") == "1"
        assert s._modality_to_param("hibrido") == "3"
        assert s._modality_to_param("") == ""
