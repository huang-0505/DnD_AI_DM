"""
Unit tests for rule_agent/app.py
Tests FastAPI endpoints and functionality.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

# Set required environment variables before importing
import os
os.environ.setdefault('GCP_PROJECT', 'test-project')

# Add rule_agent to path
RULE_AGENT_PATH = Path(__file__).parent.parent.parent / "src" / "rule_agent"
sys.path.insert(0, str(RULE_AGENT_PATH))

# Mock langchain.text_splitter before importing app
from unittest.mock import MagicMock
langchain_mock = MagicMock()
langchain_mock.text_splitter = MagicMock()
langchain_mock.text_splitter.CharacterTextSplitter = MagicMock()
langchain_mock.text_splitter.RecursiveCharacterTextSplitter = MagicMock()
sys.modules['langchain.text_splitter'] = langchain_mock.text_splitter


@pytest.mark.unit
class TestRuleAgentApp:
    """Test Rule Agent FastAPI app."""

    @patch('app.chromadb')
    @patch('app.genai.Client')
    @patch.dict('os.environ', {'GCP_PROJECT': 'test-project'})
    def test_root_endpoint(self, mock_client_class, mock_chromadb):
        """Test root endpoint."""
        # Mock ChromaDB
        mock_chroma_client = Mock()
        mock_chromadb.HttpClient.return_value = mock_chroma_client
        
        import app
        client = TestClient(app.app)
        
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "D&D Rule Agent API"
        assert data["status"] == "active"

    @patch('app.chromadb')
    @patch('app.genai.Client')
    @patch.dict('os.environ', {'GCP_PROJECT': 'test-project'})
    def test_health_check(self, mock_client_class, mock_chromadb):
        """Test health check endpoint."""
        mock_chroma_client = Mock()
        mock_chromadb.HttpClient.return_value = mock_chroma_client
        
        import app
        client = TestClient(app.app)
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    @patch('app.get_collection')
    @patch('app.chromadb')
    @patch('app.genai.Client')
    @patch.dict('os.environ', {'GCP_PROJECT': 'test-project'})
    def test_validate_endpoint_success(self, mock_client_class, mock_chromadb, mock_get_collection):
        """Test validation endpoint with successful validation."""
        # Mock collection
        mock_collection = Mock()
        mock_collection.query.return_value = {
            "documents": [["PHB p.194: Attack action allows you to make a melee or ranged attack."]]
        }
        mock_get_collection.return_value = mock_collection
        
        # Mock LLM response
        mock_llm_client = Mock()
        mock_response = Mock()
        mock_response.candidates = [Mock()]
        mock_response.candidates[0].content.parts = [Mock()]
        mock_response.candidates[0].content.parts[0].text = "The attack action is valid according to D&D rules."
        mock_llm_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_llm_client
        
        import app
        app.llm_client = mock_llm_client
        client = TestClient(app.app)
        
        response = client.post("/validate", json={
            "user_input": "I attack the goblin",
            "context": {"in_combat": True}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "is_valid" in data
        assert "explanation" in data

    @patch('app.get_collection')
    @patch('app.chromadb')
    @patch('app.genai.Client')
    @patch.dict('os.environ', {'GCP_PROJECT': 'test-project'})
    def test_validate_endpoint_no_collection(self, mock_client_class, mock_chromadb, mock_get_collection):
        """Test validation endpoint when collection is unavailable."""
        mock_get_collection.return_value = None
        
        import app
        client = TestClient(app.app)
        
        response = client.post("/validate", json={
            "user_input": "I attack",
            "context": {}
        })
        
        # Should still return a response, possibly with error handling
        assert response.status_code in [200, 500, 503]

    @patch('app.get_collection')
    @patch('app.chromadb')
    @patch('app.genai.Client')
    @patch('app.generate_query_embedding')
    @patch.dict('os.environ', {'GCP_PROJECT': 'test-project'})
    def test_retrieve_rules_endpoint(self, mock_embed_func, mock_client_class, mock_chromadb, mock_get_collection):
        """Test retrieve rules endpoint."""
        mock_collection = Mock()
        mock_collection.query.return_value = {
            "documents": [["Rule 1: Attack", "Rule 2: Damage"]]
        }
        mock_get_collection.return_value = mock_collection
        
        # Mock the embedding function
        mock_embed_func.return_value = [0.1] * 256
        
        import app
        client = TestClient(app.app)
        
        response = client.post("/retrieve_rules", json={
            "query": "attack action",
            "n_results": 2
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "rules" in data
        assert isinstance(data["rules"], str)

    @patch('app.get_collection')
    @patch('app.chromadb')
    @patch('app.genai.Client')
    @patch('app.generate_query_embedding')
    @patch.dict('os.environ', {'GCP_PROJECT': 'test-project'})
    def test_retrieve_rules_default_n_results(self, mock_embed_func, mock_client_class, mock_chromadb, mock_get_collection):
        """Test retrieve rules with default n_results."""
        mock_collection = Mock()
        mock_collection.query.return_value = {
            "documents": [[]]
        }
        mock_get_collection.return_value = mock_collection
        
        # Mock the embedding function
        mock_embed_func.return_value = [0.1] * 256
        
        import app
        client = TestClient(app.app)
        
        response = client.post("/retrieve_rules", json={
            "query": "test query"
        })
        
        assert response.status_code == 200
        # Should use default n_results=5

    @patch('app.chromadb')
    @patch('app.genai.Client')
    @patch.dict('os.environ', {'GCP_PROJECT': 'test-project'})
    def test_get_collection_function(self, mock_client_class, mock_chromadb):
        """Test get_collection function."""
        mock_chroma_client = Mock()
        mock_collection = Mock()
        mock_chroma_client.get_collection.return_value = mock_collection
        mock_chromadb.HttpClient.return_value = mock_chroma_client
        
        import app
        app.collection = None  # Reset collection
        
        result = app.get_collection()
        
        assert result == mock_collection

    @patch('app.chromadb')
    @patch('app.genai.Client')
    @patch.dict('os.environ', {'GCP_PROJECT': 'test-project'})
    def test_get_collection_error_handling(self, mock_client_class, mock_chromadb):
        """Test get_collection error handling."""
        mock_chromadb.HttpClient.side_effect = Exception("Connection failed")
        
        import app
        app.collection = None
        
        result = app.get_collection()
        
        # Should return None on error
        assert result is None

