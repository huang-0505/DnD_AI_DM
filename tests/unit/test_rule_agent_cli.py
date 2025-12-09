"""
Unit tests for rule_agent/cli.py
Tests CLI functions for embedding generation and text processing.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import os

# Set required environment variables before importing
os.environ.setdefault('GCP_PROJECT', 'test-project')

# Add rule_agent to path
RULE_AGENT_PATH = Path(__file__).parent.parent.parent / "src" / "rule_agent"
sys.path.insert(0, str(RULE_AGENT_PATH))

# Mock langchain.text_splitter before importing cli
from unittest.mock import MagicMock
langchain_mock = MagicMock()
langchain_mock.text_splitter = MagicMock()
langchain_mock.text_splitter.CharacterTextSplitter = MagicMock()
langchain_mock.text_splitter.RecursiveCharacterTextSplitter = MagicMock()
sys.modules['langchain.text_splitter'] = langchain_mock.text_splitter


@pytest.mark.unit
class TestGenerateQueryEmbedding:
    """Test generate_query_embedding function."""

    @patch('cli.llm_client')
    @patch.dict('os.environ', {'GCP_PROJECT': 'test-project'})
    def test_generate_query_embedding(self, mock_llm_client):
        """Test generating query embedding."""
        mock_response = Mock()
        mock_embedding = Mock()
        mock_embedding.values = [0.1] * 256
        mock_response.embeddings = [mock_embedding]
        mock_llm_client.models.embed_content.return_value = mock_response
        
        from cli import generate_query_embedding
        
        result = generate_query_embedding("test query")
        
        assert len(result) == 256
        assert all(isinstance(x, (int, float)) for x in result)
        mock_llm_client.models.embed_content.assert_called_once()


@pytest.mark.unit
class TestGenerateTextEmbeddings:
    """Test generate_text_embeddings function."""

    @patch('cli.llm_client')
    @patch.dict('os.environ', {'GCP_PROJECT': 'test-project'})
    def test_generate_text_embeddings_single_batch(self, mock_llm_client):
        """Test generating embeddings for small batch."""
        mock_response = Mock()
        mock_embeddings = [Mock() for _ in range(10)]
        for emb in mock_embeddings:
            emb.values = [0.1] * 256
        mock_response.embeddings = mock_embeddings
        mock_llm_client.models.embed_content.return_value = mock_response
        
        from cli import generate_text_embeddings
        
        chunks = [f"chunk {i}" for i in range(10)]
        result = generate_text_embeddings(chunks)
        
        assert len(result) == 10
        assert all(len(emb) == 256 for emb in result)

    @patch('cli.llm_client')
    @patch.dict('os.environ', {'GCP_PROJECT': 'test-project'})
    def test_generate_text_embeddings_multiple_batches(self, mock_llm_client):
        """Test generating embeddings with multiple batches."""
        mock_response = Mock()
        mock_embeddings = [Mock() for _ in range(250)]
        for emb in mock_embeddings:
            emb.values = [0.1] * 256
        mock_response.embeddings = mock_embeddings
        mock_llm_client.models.embed_content.return_value = mock_response
        
        from cli import generate_text_embeddings
        
        chunks = [f"chunk {i}" for i in range(500)]  # 2 batches
        result = generate_text_embeddings(chunks, batch_size=250)
        
        assert len(result) == 500
        assert mock_llm_client.models.embed_content.call_count == 2

    @patch('cli.llm_client')
    @patch('cli.time.sleep')
    @patch.dict('os.environ', {'GCP_PROJECT': 'test-project'})
    def test_generate_text_embeddings_retry(self, mock_sleep, mock_llm_client):
        """Test retry logic on failure."""
        # First call fails, second succeeds
        mock_response = Mock()
        mock_embeddings = [Mock() for _ in range(5)]
        for emb in mock_embeddings:
            emb.values = [0.1] * 256
        mock_response.embeddings = mock_embeddings
        
        # Import errors module to create proper APIError
        from google.genai import errors
        
        # Create a call counter to track retries
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call raises APIError (will be caught and retried)
                # APIError requires: code (int), response_json (dict with error.message structure)
                api_error = errors.APIError(
                    code=429,
                    response_json={"error": {"message": "Rate limit exceeded"}}
                )
                raise api_error
            # Second call succeeds
            return mock_response
        
        mock_llm_client.models.embed_content.side_effect = side_effect
        
        from cli import generate_text_embeddings
        
        chunks = [f"chunk {i}" for i in range(5)]
        # The function should catch the APIError, sleep, and retry
        result = generate_text_embeddings(chunks, max_retries=3, retry_delay=0.01)
        
        # Should succeed after retry
        assert len(result) == 5
        assert mock_sleep.called  # Should have slept during retry
        assert call_count[0] == 2  # Should have been called twice (1 failure + 1 success)


@pytest.mark.unit
class TestSystemInstruction:
    """Test system instruction constant."""

    @patch.dict('os.environ', {'GCP_PROJECT': 'test-project'})
    def test_system_instruction_exists(self):
        """Test that SYSTEM_INSTRUCTION is defined."""
        from cli import SYSTEM_INSTRUCTION
        
        assert isinstance(SYSTEM_INSTRUCTION, str)
        assert len(SYSTEM_INSTRUCTION) > 0
        assert "Rule Agent" in SYSTEM_INSTRUCTION or "DnD" in SYSTEM_INSTRUCTION

    @patch.dict('os.environ', {'GCP_PROJECT': 'test-project'})
    def test_generative_model_constant(self):
        """Test that GENERATIVE_MODEL is defined."""
        from cli import GENERATIVE_MODEL
        
        assert isinstance(GENERATIVE_MODEL, str)
        assert len(GENERATIVE_MODEL) > 0

