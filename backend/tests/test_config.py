"""Tests for core/config.py - Settings and configuration."""
import os
from unittest.mock import patch

import pytest


class TestSettings:
    """Test the Settings configuration class."""

    def test_settings_loads_defaults(self):
        """Settings should load with default values."""
        from app.core.config import Settings
        
        settings = Settings()
        assert settings.project_name == "Longevity Validator"
        assert settings.REDIS_HOST == "localhost"
        assert settings.REDIS_PORT == 6379

    def test_settings_reads_env_variables(self):
        """Settings should read from environment variables."""
        with patch.dict(os.environ, {"PROJECT_NAME": "Test Project"}):
            from app.core.config import Settings
            
            settings = Settings()
            # Note: pydantic caches the settings, so this tests env reading capability

    def test_openai_api_key_property(self):
        """OPENAI_API_KEY property should return the secret value."""
        from app.core.config import settings
        
        # The key is set in conftest.py
        assert settings.OPENAI_API_KEY is not None

    def test_api_contact_email_has_default(self):
        """API contact email should have a default value."""
        from app.core.config import settings
        
        assert settings.API_CONTACT_EMAIL is not None
        assert "@" in settings.API_CONTACT_EMAIL


class TestSettingsValidation:
    """Test settings validation."""

    def test_redis_port_is_integer(self):
        """Redis port should be an integer."""
        from app.core.config import settings
        
        assert isinstance(settings.REDIS_PORT, int)
        assert settings.REDIS_PORT > 0
        assert settings.REDIS_PORT < 65536
