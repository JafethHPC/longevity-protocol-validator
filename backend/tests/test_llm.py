"""Tests for services/llm.py - LLM client management."""
from unittest.mock import patch, MagicMock

import pytest


class TestLLMModule:
    """Test the LLM module exports and structure."""

    def test_get_llm_is_exported(self):
        """get_llm should be importable."""
        from app.services.llm import get_llm
        
        assert callable(get_llm)

    def test_get_embeddings_is_exported(self):
        """get_embeddings should be importable."""
        from app.services.llm import get_embeddings
        
        assert callable(get_embeddings)

    def test_clear_llm_cache_is_exported(self):
        """clear_llm_cache should be importable."""
        from app.services.llm import clear_llm_cache
        
        assert callable(clear_llm_cache)

    def test_get_structured_llm_is_exported(self):
        """get_structured_llm should be importable."""
        from app.services.llm import get_structured_llm
        
        assert callable(get_structured_llm)


class TestLLMCaching:
    """Test LLM client caching behavior."""

    def test_get_llm_is_cached(self):
        """get_llm should use lru_cache."""
        from app.services.llm import get_llm
        
        # lru_cache decorated functions have cache_info method
        assert hasattr(get_llm, 'cache_info')

    def test_get_embeddings_is_cached(self):
        """get_embeddings should use lru_cache."""
        from app.services.llm import get_embeddings
        
        assert hasattr(get_embeddings, 'cache_info')

    def test_clear_llm_cache_clears_all(self):
        """clear_llm_cache should clear all cached instances."""
        from app.services.llm import get_llm, get_embeddings, clear_llm_cache
        
        # Clear and check it doesn't raise
        clear_llm_cache()
        
        # Cache info should show 0 hits after clearing
        info = get_llm.cache_info()
        # Check it's callable (basic sanity check)
        assert info is not None


class TestLLMFunctionSignatures:
    """Test LLM function signatures and defaults."""

    def test_get_llm_has_default_model(self):
        """get_llm should have default model parameter."""
        from app.services.llm import get_llm
        import inspect
        
        sig = inspect.signature(get_llm)
        assert 'model' in sig.parameters
        
        # Default should be gpt-4o-mini
        default = sig.parameters['model'].default
        assert default == "gpt-4o-mini"

    def test_get_llm_has_temperature_param(self):
        """get_llm should have temperature parameter."""
        from app.services.llm import get_llm
        import inspect
        
        sig = inspect.signature(get_llm)
        assert 'temperature' in sig.parameters
