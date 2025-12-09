"""
Unit tests for backend/api/utils/db_tool.py
Tests DBConfig, EmbeddingGenerator, and utility functions.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import os


@pytest.mark.unit
class TestDBConfig:
    """Test DBConfig class."""

    @patch.dict(os.environ, {"GCP_PROJECT": "test-project"})
    def test_config_initialization(self):
        """Test config initialization with environment variables."""
        from api.utils.db_tool import DBConfig
        
        config = DBConfig()
        
        assert config.gcp_project == "test-project"
        assert config.gcp_location == "us-central1"  # Default
        assert config.embedding_model == "text-embedding-004"
        assert config.embedding_dimension == 256

    @patch.dict(os.environ, {"GCP_PROJECT": "test-project", "GCP_LOCATION": "us-east1"})
    def test_config_custom_location(self):
        """Test config with custom location."""
        from api.utils.db_tool import DBConfig
        
        config = DBConfig()
        
        assert config.gcp_location == "us-east1"

    @patch.dict(os.environ, {}, clear=True)
    def test_config_missing_project(self):
        """Test config raises error when GCP_PROJECT is missing."""
        from api.utils.db_tool import DBConfig
        
        with pytest.raises(ValueError, match="GCP_PROJECT.*must be set"):
            DBConfig()


@pytest.mark.unit
class TestEmbeddingGenerator:
    """Test EmbeddingGenerator class."""

    @patch.dict(os.environ, {"GCP_PROJECT": "test-project"})
    @patch('api.utils.db_tool.genai.Client')
    def test_generator_initialization(self, mock_client_class):
        """Test embedding generator initialization."""
        from api.utils.db_tool import DBConfig, EmbeddingGenerator
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        config = DBConfig()
        generator = EmbeddingGenerator(config)
        
        assert generator.config == config
        mock_client_class.assert_called_once_with(
            vertexai=True,
            project="test-project",
            location="us-central1"
        )

    @patch.dict(os.environ, {"GCP_PROJECT": "test-project"})
    @patch('api.utils.db_tool.genai.Client')
    def test_generate_single(self, mock_client_class):
        """Test generating single embedding."""
        from api.utils.db_tool import DBConfig, EmbeddingGenerator
        from google.genai import types
        
        mock_client = Mock()
        mock_embedding = Mock()
        mock_embedding.values = [0.1] * 256
        mock_response = Mock()
        mock_response.embeddings = [mock_embedding]
        mock_client.models.embed_content.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        config = DBConfig()
        generator = EmbeddingGenerator(config)
        
        result = generator.generate_single("test query")
        
        assert isinstance(result, np.ndarray)
        assert len(result) == 256
        mock_client.models.embed_content.assert_called_once()
        call_kwargs = mock_client.models.embed_content.call_args[1]
        assert call_kwargs["contents"] == "test query"
        assert isinstance(call_kwargs["config"], types.EmbedContentConfig)

    @patch.dict(os.environ, {"GCP_PROJECT": "test-project"})
    @patch('api.utils.db_tool.genai.Client')
    def test_generate_single_different_dimension(self, mock_client_class):
        """Test generating embedding with different dimension."""
        from api.utils.db_tool import DBConfig, EmbeddingGenerator
        
        mock_client = Mock()
        mock_embedding = Mock()
        mock_embedding.values = [0.1] * 128
        mock_response = Mock()
        mock_response.embeddings = [mock_embedding]
        mock_client.models.embed_content.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        config = DBConfig()
        config.embedding_dimension = 128
        generator = EmbeddingGenerator(config)
        
        result = generator.generate_single("test")
        
        assert len(result) == 128


@pytest.mark.unit
class TestCosineSimilarity:
    """Test cosine_similarity function."""

    def test_cosine_similarity_identical(self):
        """Test cosine similarity with identical vectors."""
        from api.utils.db_tool import cosine_similarity
        
        query = np.array([1.0, 0.0, 0.0])
        corpus = np.array([[1.0, 0.0, 0.0]])
        
        result = cosine_similarity(query, corpus)
        
        assert len(result) == 1
        assert abs(result[0] - 1.0) < 0.001  # Should be 1.0 for identical vectors

    def test_cosine_similarity_orthogonal(self):
        """Test cosine similarity with orthogonal vectors."""
        from api.utils.db_tool import cosine_similarity
        
        query = np.array([1.0, 0.0, 0.0])
        corpus = np.array([[0.0, 1.0, 0.0]])
        
        result = cosine_similarity(query, corpus)
        
        assert len(result) == 1
        assert abs(result[0]) < 0.001  # Should be ~0 for orthogonal vectors

    def test_cosine_similarity_multiple(self):
        """Test cosine similarity with multiple corpus vectors."""
        from api.utils.db_tool import cosine_similarity
        
        query = np.array([1.0, 0.0, 0.0])
        corpus = np.array([
            [1.0, 0.0, 0.0],  # Identical
            [0.0, 1.0, 0.0],  # Orthogonal
            [0.707, 0.707, 0.0]  # 45 degrees
        ])
        
        result = cosine_similarity(query, corpus)
        
        assert len(result) == 3
        assert abs(result[0] - 1.0) < 0.1  # Identical
        assert abs(result[1]) < 0.1  # Orthogonal
        assert 0.5 < result[2] < 1.0  # 45 degrees

    def test_cosine_similarity_normalized(self):
        """Test cosine similarity handles normalization correctly."""
        from api.utils.db_tool import cosine_similarity
        
        query = np.array([2.0, 0.0, 0.0])  # Different magnitude
        corpus = np.array([[1.0, 0.0, 0.0]])
        
        result = cosine_similarity(query, corpus)
        
        # Should still be 1.0 after normalization
        assert abs(result[0] - 1.0) < 0.001


@pytest.mark.unit
class TestRetrieveTopK:
    """Test retrieve_top_k convenience function."""

    @patch.dict(os.environ, {"GCP_PROJECT": "test-project"})
    @patch('api.utils.db_tool.pd.read_json')
    @patch('api.utils.db_tool.EmbeddingGenerator')
    def test_retrieve_top_k_basic(self, mock_generator_class, mock_read_json):
        """Test basic top-k retrieval."""
        from api.utils.db_tool import retrieve_top_k
        
        # Mock DataFrame
        mock_df = Mock()
        mock_df.__getitem__ = Mock(return_value=Mock())
        mock_df.__getitem__.return_value.values = [
            np.array([0.1] * 256),
            np.array([0.2] * 256),
            np.array([0.3] * 256)
        ]
        mock_df.iloc = Mock()
        mock_df.iloc.__getitem__ = Mock(return_value=Mock())
        mock_df.iloc.__getitem__.return_value.copy.return_value = Mock()
        mock_df.iloc.__getitem__.return_value.copy.return_value.__getitem__ = Mock(return_value=Mock())
        mock_df.iloc.__getitem__.return_value.copy.return_value.__getitem__.return_value.tolist.return_value = [1, 2]
        
        mock_read_json.return_value = mock_df
        
        # Mock embedding generator
        mock_generator = Mock()
        mock_generator.generate_single.return_value = np.array([0.15] * 256)
        mock_generator_class.return_value = mock_generator
        
        result = retrieve_top_k("test query", k=2)
        
        assert isinstance(result, list)
        mock_generator.generate_single.assert_called_once_with("test query")

    @patch.dict(os.environ, {"GCP_PROJECT": "test-project"})
    @patch('api.utils.db_tool.pd.read_json')
    @patch('api.utils.db_tool.EmbeddingGenerator')
    def test_retrieve_top_k_custom_file(self, mock_generator_class, mock_read_json):
        """Test top-k retrieval with custom embeddings file."""
        from api.utils.db_tool import retrieve_top_k
        
        mock_df = Mock()
        mock_df.__getitem__ = Mock(return_value=Mock())
        mock_df.__getitem__.return_value.values = [np.array([0.1] * 256)]
        mock_df.iloc = Mock()
        mock_df.iloc.__getitem__ = Mock(return_value=Mock())
        mock_df.iloc.__getitem__.return_value.copy.return_value = Mock()
        mock_df.iloc.__getitem__.return_value.copy.return_value.__getitem__ = Mock(return_value=Mock())
        mock_df.iloc.__getitem__.return_value.copy.return_value.__getitem__.return_value.tolist.return_value = [1]
        
        mock_read_json.return_value = mock_df
        
        mock_generator = Mock()
        mock_generator.generate_single.return_value = np.array([0.1] * 256)
        mock_generator_class.return_value = mock_generator
        
        result = retrieve_top_k("query", embeddings_file="custom.jsonl", k=1)
        
        mock_read_json.assert_called_once_with("custom.jsonl", lines=True)

