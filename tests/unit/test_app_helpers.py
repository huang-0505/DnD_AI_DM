"""
Unit tests for orchestrator/app.py helper functions.
Tests detect_combat_trigger, detect_combat_end, and other utility functions.
"""

import pytest
import sys
import os
import importlib.util
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock

# Set required environment variables before importing
os.environ.setdefault('GCP_PROJECT', 'test-project')

# Mock langchain.text_splitter before importing (to avoid import errors from rule_agent/cli.py)
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
class TestCombatDetection:
    """Test combat trigger and end detection functions."""

    @patch.object(orchestrator_app, 'client')
    def test_detect_combat_trigger_yes(self, mock_client):
        """Test detecting combat trigger when present."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "YES"
        mock_client.chat.completions.create.return_value = mock_response
        
        result = orchestrator_app.detect_combat_trigger("Enemies appear and attack!")
        assert result is True

    @patch.object(orchestrator_app, 'client')
    def test_detect_combat_trigger_no(self, mock_client):
        """Test detecting no combat trigger."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "NO"
        mock_client.chat.completions.create.return_value = mock_response
        
        result = orchestrator_app.detect_combat_trigger("You walk through the peaceful village.")
        assert result is False

    @patch.object(orchestrator_app, 'client')
    def test_detect_combat_trigger_case_insensitive(self, mock_client):
        """Test combat detection is case-insensitive."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "yes"
        mock_client.chat.completions.create.return_value = mock_response
        
        result = orchestrator_app.detect_combat_trigger("You are ambushed!")
        assert result is True

    def test_detect_combat_trigger_no_client(self):
        """Test combat detection when client is unavailable."""
        original_client = orchestrator_app.client
        orchestrator_app.client = None
        try:
            result = orchestrator_app.detect_combat_trigger("Enemies attack!")
            assert result is False
        finally:
            orchestrator_app.client = original_client

    @patch.object(orchestrator_app, 'client')
    def test_detect_combat_trigger_error(self, mock_client):
        """Test combat detection handles errors gracefully."""
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        result = orchestrator_app.detect_combat_trigger("Enemies attack!")
        assert result is False

    def test_detect_combat_end_true(self):
        """Test detecting combat end when battle_over is True."""
        combat_state = {"battle_over": True, "round": 5}
        result = orchestrator_app.detect_combat_end(combat_state)
        assert result is True

    def test_detect_combat_end_false(self):
        """Test detecting combat not ended when battle_over is False."""
        combat_state = {"battle_over": False, "round": 2}
        result = orchestrator_app.detect_combat_end(combat_state)
        assert result is False

    def test_detect_combat_end_missing_key(self):
        """Test detecting combat end when battle_over key is missing."""
        combat_state = {"round": 3}
        result = orchestrator_app.detect_combat_end(combat_state)
        assert result is False


@pytest.mark.unit
class TestNarratorAgent:
    """Test narrator agent communication functions."""

    @patch.object(orchestrator_app, 'llm_client')
    @patch.object(orchestrator_app, 'NARRATOR_ENDPOINT', 'http://test-endpoint')
    def test_call_narrator_agent_success(self, mock_llm):
        """Test successful narrator agent call."""
        # Mock the LLM response properly
        mock_candidate = Mock()
        mock_candidate.content.parts = [Mock()]
        mock_candidate.content.parts[0].text = "You see a door ahead.\n\nCHOICES:\n1. Open it\n2. Look around\n3. Go back"
        mock_candidate.finish_reason = 1  # Normal completion
        
        mock_response = Mock()
        mock_response.candidates = [mock_candidate]
        mock_response.text = "You see a door ahead.\n\nCHOICES:\n1. Open it\n2. Look around\n3. Go back"
        mock_llm.models.generate_content.return_value = mock_response
        
        result = orchestrator_app.call_narrator_agent("I look around")
        
        assert result["agent"] == "narrator"
        assert "result" in result
        # Choices may be None if extraction fails, but result should exist
        assert result["result"] is not None

    def test_call_narrator_agent_fallback(self):
        """Test narrator agent fallback when unavailable."""
        original_llm = orchestrator_app.llm_client
        orchestrator_app.llm_client = None
        try:
            result = orchestrator_app.call_narrator_agent("I look around")
            assert result["agent"] == "narrator"
            assert "unavailable" in result["result"].lower()
            assert result["choices"] is None
        finally:
            orchestrator_app.llm_client = original_llm

    def test_call_narrator_agent_no_endpoint(self):
        """Test narrator agent when endpoint is not configured."""
        original_endpoint = orchestrator_app.NARRATOR_ENDPOINT
        orchestrator_app.NARRATOR_ENDPOINT = None
        try:
            result = orchestrator_app.call_narrator_agent("I look around")
            assert result["agent"] == "narrator"
            assert "unavailable" in result["result"].lower()
        finally:
            orchestrator_app.NARRATOR_ENDPOINT = original_endpoint


@pytest.mark.unit
class TestCombatAgent:
    """Test combat agent communication functions."""

    @patch('requests.post')
    def test_call_combat_agent_success(self, mock_post):
        """Test successful combat agent call."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "session_id": "combat-123",
            "state": {"battle_over": False}
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # Use the correct function name
        result = orchestrator_app.call_combat_agent_start()
        
        assert "session_id" in result or "result" in result
        # The function returns a dict with combat state info

    @patch('requests.post')
    def test_call_combat_agent_error(self, mock_post):
        """Test combat agent error handling."""
        mock_post.side_effect = Exception("Connection error")
        
        # Use the correct function name
        result = orchestrator_app.call_combat_agent_start()
        
        # Should handle error gracefully
        assert isinstance(result, dict)
