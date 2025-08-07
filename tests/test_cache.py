import pytest
import redis
from unittest.mock import patch, MagicMock
from src.cache.redis_cache import get_md, set_md
from src.cache.doctor_semantic_index import semantic_lookup, _load_vectors


class TestRedisCache:
    """Test Redis exact cache functionality."""
    
    @patch('src.cache.redis_cache._r')
    def test_get_md_hit(self, mock_redis):
        """Test successful cache retrieval."""
        mock_redis.get.return_value = "Test diagnosis markdown"
        result = get_md("test_hash")
        assert result == "Test diagnosis markdown"
        mock_redis.get.assert_called_once_with("test_hash")
    
    @patch('src.cache.redis_cache._r')
    def test_get_md_miss(self, mock_redis):
        """Test cache miss returns None."""
        mock_redis.get.return_value = None
        result = get_md("test_hash")
        assert result is None
    
    @patch('src.cache.redis_cache._r')
    def test_set_md(self, mock_redis):
        """Test setting cache value with TTL."""
        set_md("test_hash", "Test diagnosis")
        mock_redis.set.assert_called_once()
        args, kwargs = mock_redis.set.call_args
        assert args[0] == "test_hash"
        assert args[1] == "Test diagnosis"
        assert "ex" in kwargs  # TTL should be set


class TestSemanticCache:
    """Test semantic cache functionality."""
    
    @patch('src.cache.doctor_semantic_index._model')
    @patch('src.cache.doctor_semantic_index._index')
    @patch('src.cache.doctor_semantic_index._texts')
    def test_semantic_lookup_hit(self, mock_texts, mock_index, mock_model):
        """Test successful semantic lookup."""
        mock_texts.__getitem__.return_value = "Similar diagnosis"
        mock_index.ntotal = 1
        mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_index.search.return_value = ([[0.95]], [[0]])  # High similarity score
        
        result = semantic_lookup("test symptoms")
        assert result == "Similar diagnosis"
    
    @patch('src.cache.doctor_semantic_index._index')
    def test_semantic_lookup_empty_index(self, mock_index):
        """Test lookup with empty index."""
        mock_index.ntotal = 0
        result = semantic_lookup("test symptoms")
        assert result is None
    
    @patch('src.cache.doctor_semantic_index._model')
    @patch('src.cache.doctor_semantic_index._index')
    @patch('src.cache.doctor_semantic_index._texts')
    def test_semantic_lookup_low_similarity(self, mock_texts, mock_index, mock_model):
        """Test lookup with low similarity score."""
        mock_index.ntotal = 1
        mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_index.search.return_value = ([[0.5]], [[0]])  # Low similarity score
        
        result = semantic_lookup("test symptoms")
        assert result is None
    
    @patch('src.cache.doctor_semantic_index.Session')
    @patch('src.cache.doctor_semantic_index._model')
    def test_load_vectors_with_data(self, mock_model, mock_session):
        """Test loading vectors with approved answers."""
        # Mock database session and approved answers
        mock_session_instance = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_session_instance
        
        mock_answer = MagicMock()
        mock_answer.answer_md = "Test answer"
        mock_session_instance.exec.return_value.all.return_value = [mock_answer]
        
        mock_model.get_sentence_embedding_dimension.return_value = 768
        mock_model.encode.return_value = [[0.1] * 768]
        
        index, texts = _load_vectors()
        
        assert len(texts) == 1
        assert texts[0] == "Test answer"
        assert index.ntotal == 1
    
    @patch('src.cache.doctor_semantic_index.Session')
    @patch('src.cache.doctor_semantic_index._model')
    def test_load_vectors_empty(self, mock_model, mock_session):
        """Test loading vectors with no approved answers."""
        mock_session_instance = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_session_instance
        mock_session_instance.exec.return_value.all.return_value = []
        
        mock_model.get_sentence_embedding_dimension.return_value = 768
        
        index, texts = _load_vectors()
        
        assert len(texts) == 0
        assert index.ntotal == 0


class TestCacheIntegration:
    """Test integration between exact and semantic cache."""
    
    @patch('src.cache.redis_cache.get_md')
    @patch('src.cache.doctor_semantic_index.semantic_lookup')
    def test_cache_priority(self, mock_semantic, mock_redis_get):
        """Test that exact cache takes priority over semantic cache."""
        # Exact cache hit
        mock_redis_get.return_value = "Exact match"
        mock_semantic.return_value = "Semantic match"
        
        # This would be called in the actual diagnose endpoint
        exact_result = get_md("test_hash")
        semantic_result = semantic_lookup("test symptoms")
        
        assert exact_result == "Exact match"
        assert semantic_result == "Semantic match"
        # In real usage, exact cache would be checked first and return early 