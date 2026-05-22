import pytest
import config


class TestConfig:
    def test_search_profiles_exists(self):
        assert hasattr(config, "SEARCH_PROFILES")
        assert len(config.SEARCH_PROFILES) > 0

    def test_profile_structure(self):
        for profile in config.SEARCH_PROFILES:
            assert "name" in profile
            assert "keywords" in profile
            assert "location" in profile
            assert "modality" in profile
            assert isinstance(profile["keywords"], list)

    def test_portals_enabled(self):
        assert hasattr(config, "PORTALS")
        for key in ["computrabajo", "trabajando", "laborum", "linkedin"]:
            assert key in config.PORTALS

    def test_cache_config(self):
        assert hasattr(config, "CACHE_ENABLED")
        assert isinstance(config.CACHE_ENABLED, bool)
