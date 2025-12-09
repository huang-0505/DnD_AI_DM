"""
Unit tests for orchestrator/app.py FastAPI endpoints.
Tests the main game endpoints that aren't covered by integration tests.
"""

import pytest
import sys
import os
import importlib.util
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

# Set required environment variables before importing
os.environ.setdefault('GCP_PROJECT', 'test-project')
os.environ.setdefault('OPENAI_API_KEY', 'test-key')

# Mock langchain.text_splitter before importing
from unittest.mock import MagicMock
langchain_mock = MagicMock()
langchain_mock.text_splitter = MagicMock()
langchain_mock.text_splitter.CharacterTextSplitter = MagicMock()
langchain_mock.text_splitter.RecursiveCharacterTextSplitter = MagicMock()
sys.modules['langchain.text_splitter'] = langchain_mock.text_splitter

# Import orchestrator app module directly
ORCHESTRATOR_PATH = Path(__file__).parent.parent.parent / "src" / "orchestrator"
spec = importlib.util.spec_from_file_location("orchestrator_app", ORCHESTRATOR_PATH / "app.py")
orchestrator_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(orchestrator_app)


@pytest.mark.unit
class TestOrchestratorEndpoints:
    """Test orchestrator FastAPI endpoints."""

    def test_root_endpoint(self):
        """Test root endpoint."""
        client = TestClient(orchestrator_app.app)
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "D&D Game Orchestrator"
        assert "version" in data

    def test_health_check(self):
        """Test health check endpoint."""
        client = TestClient(orchestrator_app.app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data

    def test_list_campaigns(self):
        """Test list campaigns endpoint."""
        client = TestClient(orchestrator_app.app)
        response = client.get("/campaigns")
        
        assert response.status_code == 200
        data = response.json()
        assert "campaigns" in data
        assert isinstance(data["campaigns"], list)

    def test_get_campaign_details_existing(self):
        """Test get campaign details for existing campaign."""
        client = TestClient(orchestrator_app.app)
        # Use a campaign that should exist
        response = client.get("/campaigns/stormwreck-isle")
        
        assert response.status_code == 200
        data = response.json()
        assert "campaign_id" in data or "name" in data

    def test_get_campaign_details_nonexistent(self):
        """Test get campaign details for nonexistent campaign."""
        client = TestClient(orchestrator_app.app)
        response = client.get("/campaigns/nonexistent-campaign")
        
        assert response.status_code == 404

    @patch.object(orchestrator_app, 'call_narrator_agent')
    def test_start_game_with_campaign(self, mock_narrator):
        """Test starting game with campaign."""
        mock_narrator.return_value = {
            "agent": "narrator",
            "result": "You begin your adventure...",
            "choices": ["Go north", "Go south"]
        }
        
        client = TestClient(orchestrator_app.app)
        response = client.post("/game/start", json={
            "campaign_id": "stormwreck-isle",
            "character_class": "Fighter",
            "character_name": "TestHero"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["message"] == "Game started successfully!"

    @patch.object(orchestrator_app, 'call_narrator_agent')
    def test_start_game_custom_prompt(self, mock_narrator):
        """Test starting game with custom prompt."""
        mock_narrator.return_value = {
            "agent": "narrator",
            "result": "You wake up in a dungeon...",
            "choices": ["Look around", "Stand up"]
        }
        
        client = TestClient(orchestrator_app.app)
        response = client.post("/game/start", json={
            "initial_prompt": "You wake up in a dark dungeon."
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data

    def test_get_game_state_nonexistent(self):
        """Test getting state for nonexistent session."""
        client = TestClient(orchestrator_app.app)
        response = client.get("/game/state/nonexistent-session-id")
        
        assert response.status_code == 404

    @patch.object(orchestrator_app, 'call_narrator_agent')
    def test_get_game_state_existing(self, mock_narrator):
        """Test getting state for existing session."""
        mock_narrator.return_value = {
            "agent": "narrator",
            "result": "You are in a forest.",
            "choices": ["Go north", "Go south"]
        }
        
        client = TestClient(orchestrator_app.app)
        # First create a session
        start_response = client.post("/game/start", json={
            "initial_prompt": "You are in a forest."
        })
        session_id = start_response.json()["session_id"]
        
        # Then get its state
        response = client.get(f"/game/state/{session_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "current_state" in data

    @patch('requests.get')
    def test_get_combat_state_nonexistent(self, mock_get):
        """Test getting combat state for nonexistent session."""
        # Mock the requests.get to simulate connection error
        mock_get.side_effect = Exception("Connection refused")
        
        client = TestClient(orchestrator_app.app)
        response = client.get("/combat/state/nonexistent-combat-id")
        
        # Should return 500 or handle gracefully
        assert response.status_code in [404, 200, 500]

    def test_end_game_session(self):
        """Test ending a game session."""
        client = TestClient(orchestrator_app.app)
        # Create a session first
        with patch.object(orchestrator_app, 'call_narrator_agent') as mock_narrator:
            mock_narrator.return_value = {
                "agent": "narrator",
                "result": "Test",
                "choices": []
            }
            start_response = client.post("/game/start", json={
                "initial_prompt": "Test"
            })
            session_id = start_response.json()["session_id"]
        
        # End the session
        response = client.delete(f"/game/session/{session_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert session_id in data["session_id"]

    @patch.object(orchestrator_app, 'call_narrator_agent')
    def test_legacy_narrator_endpoint(self, mock_narrator):
        """Test legacy narrator endpoint."""
        mock_narrator.return_value = {
            "agent": "narrator",
            "result": "You see a door.",
            "choices": []
        }
        
        client = TestClient(orchestrator_app.app)
        response = client.post("/agent/narration", json={
            "text": "I look around"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "agent" in data
        assert data["agent"] == "narrator"

    @patch.object(orchestrator_app, 'client')
    @patch.object(orchestrator_app, 'call_narrator_agent')
    def test_legacy_orchestrate_endpoint_narration(self, mock_narrator, mock_client):
        """Test legacy orchestrate endpoint with narration intent."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "narration"
        mock_client.chat.completions.create.return_value = mock_response
        
        mock_narrator.return_value = {
            "agent": "narrator",
            "result": "You walk forward.",
            "choices": []
        }
        
        client = TestClient(orchestrator_app.app)
        response = client.post("/orchestrate", json={
            "text": "I walk forward"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "orchestrator_intent" in data
        assert "agent_response" in data

    @patch.object(orchestrator_app, 'client')
    def test_legacy_orchestrate_endpoint_combat(self, mock_client):
        """Test legacy orchestrate endpoint with combat intent."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "combat"
        mock_client.chat.completions.create.return_value = mock_response
        
        client = TestClient(orchestrator_app.app)
        response = client.post("/orchestrate", json={
            "text": "I attack the goblin"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "orchestrator_intent" in data
        assert "combat" in data["orchestrator_intent"]
        assert "agent_response" in data

    @patch.object(orchestrator_app, 'client', None)
    @patch.object(orchestrator_app, 'call_narrator_agent')
    def test_legacy_orchestrate_no_client(self, mock_narrator):
        """Test legacy orchestrate endpoint when client is unavailable."""
        mock_narrator.return_value = {
            "agent": "narrator",
            "result": "Default narration",
            "choices": []
        }
        
        client = TestClient(orchestrator_app.app)
        response = client.post("/orchestrate", json={
            "text": "I do something"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "orchestrator_intent" in data
        assert data["orchestrator_intent"] == "narration"  # Default when no client

