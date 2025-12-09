"""
Unit tests for rule_agent/semantic_splitter.py
Tests SemanticChunker and helper functions.
"""

import pytest
import sys
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch

# Add rule_agent to path
RULE_AGENT_PATH = Path(__file__).parent.parent.parent / "src" / "rule_agent"
sys.path.insert(0, str(RULE_AGENT_PATH))

from semantic_splitter import (
    SemanticChunker,
    combine_sentences,
    calculate_cosine_distances,
    BREAKPOINT_DEFAULTS
)


@pytest.mark.unit
class TestCombineSentences:
    """Test combine_sentences function."""

    def test_combine_sentences_default_buffer(self):
        """Test combining sentences with default buffer size."""
        sentences = [
            {"sentence": "First sentence."},
            {"sentence": "Second sentence."},
            {"sentence": "Third sentence."}
        ]
        
        result = combine_sentences(sentences, buffer_size=1)
        
        assert len(result) == 3
        assert "combined_sentence" in result[0]
        assert "First sentence." in result[0]["combined_sentence"]
        assert "Second sentence." in result[0]["combined_sentence"]

    def test_combine_sentences_larger_buffer(self):
        """Test combining sentences with larger buffer."""
        sentences = [
            {"sentence": "First."},
            {"sentence": "Second."},
            {"sentence": "Third."}
        ]
        
        result = combine_sentences(sentences, buffer_size=2)
        
        assert len(result) == 3
        # First sentence should include next 2
        assert "Second." in result[0]["combined_sentence"]
        assert "Third." in result[0]["combined_sentence"]

    def test_combine_sentences_zero_buffer(self):
        """Test combining sentences with zero buffer."""
        sentences = [
            {"sentence": "First."},
            {"sentence": "Second."}
        ]
        
        result = combine_sentences(sentences, buffer_size=0)
        
        assert len(result) == 2
        assert result[0]["combined_sentence"] == "First."


@pytest.mark.unit
class TestCalculateCosineDistances:
    """Test calculate_cosine_distances function."""

    def test_calculate_cosine_distances(self):
        """Test calculating cosine distances between sentences."""
        # Create mock embeddings (similar embeddings should have low distance)
        embedding1 = np.array([1.0, 0.0, 0.0])
        embedding2 = np.array([0.9, 0.1, 0.0])  # Similar to embedding1
        embedding3 = np.array([0.0, 1.0, 0.0])  # Different from embedding1
        
        sentences = [
            {
                "sentence": "First sentence.",
                "combined_sentence": "First sentence.",
                "combined_sentence_embedding": embedding1
            },
            {
                "sentence": "Second sentence.",
                "combined_sentence": "Second sentence.",
                "combined_sentence_embedding": embedding2
            },
            {
                "sentence": "Third sentence.",
                "combined_sentence": "Third sentence.",
                "combined_sentence_embedding": embedding3
            }
        ]
        
        distances, updated_sentences = calculate_cosine_distances(sentences)
        
        assert len(distances) == 2  # n-1 distances for n sentences
        assert all(0 <= d <= 1 for d in distances)  # Cosine distance is between 0 and 1
        assert "distance_to_next" in updated_sentences[0]
        assert "distance_to_next" in updated_sentences[1]

    def test_calculate_cosine_distances_single_sentence(self):
        """Test cosine distances with single sentence."""
        sentences = [
            {
                "sentence": "Only sentence.",
                "combined_sentence": "Only sentence.",
                "combined_sentence_embedding": np.array([1.0, 0.0])
            }
        ]
        
        distances, updated_sentences = calculate_cosine_distances(sentences)
        
        assert len(distances) == 0  # No distances for single sentence


@pytest.mark.unit
class TestSemanticChunker:
    """Test SemanticChunker class."""

    def test_chunker_initialization_defaults(self):
        """Test chunker initialization with defaults."""
        mock_embedding_func = Mock(return_value=[[0.1] * 256])
        
        chunker = SemanticChunker(embedding_function=mock_embedding_func)
        
        assert chunker.buffer_size == 1
        assert chunker.breakpoint_threshold_type == "percentile"
        assert chunker.breakpoint_threshold_amount == BREAKPOINT_DEFAULTS["percentile"]
        assert chunker.number_of_chunks is None

    def test_chunker_initialization_custom(self):
        """Test chunker initialization with custom parameters."""
        mock_embedding_func = Mock()
        
        chunker = SemanticChunker(
            buffer_size=2,
            breakpoint_threshold_type="standard_deviation",
            breakpoint_threshold_amount=2.5,
            number_of_chunks=5,
            embedding_function=mock_embedding_func
        )
        
        assert chunker.buffer_size == 2
        assert chunker.breakpoint_threshold_type == "standard_deviation"
        assert chunker.breakpoint_threshold_amount == 2.5
        assert chunker.number_of_chunks == 5

    def test_split_text_single_sentence(self):
        """Test splitting text with single sentence."""
        mock_embedding_func = Mock(return_value=[[0.1] * 256])
        chunker = SemanticChunker(embedding_function=mock_embedding_func)
        
        result = chunker.split_text("Single sentence.")
        
        assert result == ["Single sentence."]

    def test_split_text_multiple_sentences(self):
        """Test splitting text with multiple sentences."""
        # Mock embedding function to return different embeddings
        def mock_embedding(texts, batch_size=50):
            # Return embeddings that create clear breakpoints
            return [[0.1] * 256 if i < 2 else [0.9] * 256 for i in range(len(texts))]
        
        chunker = SemanticChunker(
            embedding_function=mock_embedding,
            breakpoint_threshold_type="percentile",
            breakpoint_threshold_amount=50  # Lower threshold for testing
        )
        
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        result = chunker.split_text(text)
        
        assert len(result) >= 1
        assert all(isinstance(chunk, str) for chunk in result)

    def test_calculate_breakpoint_threshold_percentile(self):
        """Test percentile threshold calculation."""
        mock_embedding_func = Mock()
        chunker = SemanticChunker(
            breakpoint_threshold_type="percentile",
            breakpoint_threshold_amount=75,
            embedding_function=mock_embedding_func
        )
        
        distances = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        threshold, _ = chunker._calculate_breakpoint_threshold(distances)
        
        expected = np.percentile(distances, 75)
        assert abs(threshold - expected) < 0.01

    def test_calculate_breakpoint_threshold_standard_deviation(self):
        """Test standard deviation threshold calculation."""
        mock_embedding_func = Mock()
        chunker = SemanticChunker(
            breakpoint_threshold_type="standard_deviation",
            breakpoint_threshold_amount=2.0,
            embedding_function=mock_embedding_func
        )
        
        distances = [0.1, 0.2, 0.3, 0.4, 0.5]
        threshold, _ = chunker._calculate_breakpoint_threshold(distances)
        
        expected = np.mean(distances) + 2.0 * np.std(distances)
        assert abs(threshold - expected) < 0.01

    def test_calculate_breakpoint_threshold_interquartile(self):
        """Test interquartile threshold calculation."""
        mock_embedding_func = Mock()
        chunker = SemanticChunker(
            breakpoint_threshold_type="interquartile",
            breakpoint_threshold_amount=1.5,
            embedding_function=mock_embedding_func
        )
        
        distances = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        threshold, _ = chunker._calculate_breakpoint_threshold(distances)
        
        q1, q3 = np.percentile(distances, [25, 75])
        iqr = q3 - q1
        expected = np.mean(distances) + 1.5 * iqr
        assert abs(threshold - expected) < 0.01

    def test_calculate_breakpoint_threshold_invalid_type(self):
        """Test invalid threshold type raises error."""
        mock_embedding_func = Mock()
        # Create chunker with valid type first, then change it to invalid
        chunker = SemanticChunker(
            breakpoint_threshold_type="percentile",
            embedding_function=mock_embedding_func
        )
        chunker.breakpoint_threshold_type = "invalid_type"
        
        with pytest.raises(ValueError, match="unexpected.*breakpoint_threshold_type"):
            chunker._calculate_breakpoint_threshold([0.1, 0.2, 0.3])

    def test_threshold_from_clusters(self):
        """Test threshold calculation from number of chunks."""
        mock_embedding_func = Mock()
        chunker = SemanticChunker(
            number_of_chunks=3,
            embedding_function=mock_embedding_func
        )
        
        distances = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        threshold = chunker._threshold_from_clusters(distances)
        
        assert 0 <= threshold <= 1

    def test_threshold_from_clusters_none(self):
        """Test threshold_from_clusters raises error when number_of_chunks is None."""
        mock_embedding_func = Mock()
        chunker = SemanticChunker(embedding_function=mock_embedding_func)
        
        with pytest.raises(ValueError, match="number_of_chunks.*None"):
            chunker._threshold_from_clusters([0.1, 0.2, 0.3])

    def test_create_documents(self):
        """Test creating documents from texts."""
        from langchain_core.documents import Document
        
        # Mock embedding function to return embeddings for each combined sentence
        def mock_embed_func(texts, batch_size=50):
            # Return one embedding per text
            return [[0.1] * 256 for _ in texts]
        
        chunker = SemanticChunker(embedding_function=mock_embed_func)
        
        texts = ["First text. Second sentence.", "Another text."]
        documents = chunker.create_documents(texts)
        
        assert len(documents) >= 1  # At least one document per text
        assert all(isinstance(doc, Document) for doc in documents)
        assert all(doc.page_content for doc in documents)

    def test_create_documents_with_metadata(self):
        """Test creating documents with metadata."""
        from langchain_core.documents import Document
        
        mock_embedding_func = Mock(return_value=[[0.1] * 256])
        chunker = SemanticChunker(embedding_function=mock_embedding_func)
        
        texts = ["Test text."]
        metadatas = [{"source": "test", "page": 1}]
        documents = chunker.create_documents(texts, metadatas=metadatas)
        
        assert len(documents) >= 1
        assert documents[0].metadata["source"] == "test"
        assert documents[0].metadata["page"] == 1

    def test_create_documents_with_start_index(self):
        """Test creating documents with start index tracking."""
        from langchain_core.documents import Document
        
        mock_embedding_func = Mock(return_value=[[0.1] * 256])
        chunker = SemanticChunker(
            add_start_index=True,
            embedding_function=mock_embedding_func
        )
        
        texts = ["Test text."]
        documents = chunker.create_documents(texts)
        
        assert len(documents) >= 1
        assert "start_index" in documents[0].metadata

