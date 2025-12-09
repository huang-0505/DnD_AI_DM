"""
Unit tests for orchestrator/rule_validator.py
Tests RuleValidator class functionality.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, Mock

# Add orchestrator to path
ORCHESTRATOR_PATH = Path(__file__).parent.parent.parent / "src" / "orchestrator"
sys.path.insert(0, str(ORCHESTRATOR_PATH))

from rule_validator import RuleValidator


@pytest.mark.unit
class TestRuleValidator:
    """Test RuleValidator class functionality."""

    def test_validator_initialization(self):
        """Test creating a validator with default URL."""
        validator = RuleValidator()
        assert validator.rule_agent_url == "http://rule-agent:9002"

    def test_validator_initialization_custom_url(self):
        """Test creating a validator with custom URL."""
        custom_url = "http://custom-rule-agent:9002"
        validator = RuleValidator(rule_agent_url=custom_url)
        assert validator.rule_agent_url == custom_url

    @patch('rule_validator.requests.post')
    def test_validate_action_success(self, mock_post):
        """Test successful action validation."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "is_valid": True,
            "validation_type": "valid",
            "explanation": "Action is valid according to D&D rules",
            "rule_text": "PHB p.194: Attack action"
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        validator = RuleValidator(rule_agent_url="http://test:9002")
        result = validator.validate_action(
            user_input="I attack the goblin",
            game_context={"in_combat": True}
        )

        assert result["is_valid"] is True
        assert result["validation_type"] == "valid"
        assert "explanation" in result
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://test:9002/validate"
        assert call_args[1]["json"]["user_input"] == "I attack the goblin"
        assert call_args[1]["json"]["context"]["in_combat"] is True

    @patch('rule_validator.requests.post')
    def test_validate_action_sabotage(self, mock_post):
        """Test sabotage detection."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "is_valid": False,
            "validation_type": "sabotage",
            "explanation": "Sabotage detected",
            "rule_text": ""
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        validator = RuleValidator()
        result = validator.validate_action(
            user_input="I want to break the game",
            game_context={}
        )

        assert result["is_valid"] is False
        assert result["validation_type"] == "sabotage"

    @patch('rule_validator.requests.post')
    def test_validate_action_connection_error(self, mock_post):
        """Test handling connection errors."""
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError()

        validator = RuleValidator()
        result = validator.validate_action(
            user_input="I attack",
            game_context={}
        )

        assert result["is_valid"] is True
        assert result["validation_type"] == "no_validation"
        assert "unavailable" in result["explanation"].lower()

    @patch('rule_validator.requests.post')
    def test_validate_action_timeout(self, mock_post):
        """Test handling timeout errors."""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()

        validator = RuleValidator()
        result = validator.validate_action(
            user_input="I attack",
            game_context={}
        )

        assert result["is_valid"] is True
        assert result["validation_type"] == "no_validation"
        assert "timeout" in result["explanation"].lower()

    @patch('rule_validator.requests.post')
    def test_validate_action_general_error(self, mock_post):
        """Test handling general errors."""
        mock_post.side_effect = Exception("Unexpected error")

        validator = RuleValidator()
        result = validator.validate_action(
            user_input="I attack",
            game_context={}
        )

        assert result["is_valid"] is True
        assert result["validation_type"] == "error"
        assert "error" in result["explanation"].lower()

    def test_is_sabotage(self):
        """Test sabotage detection helper."""
        validator = RuleValidator()
        
        result_valid = {"validation_type": "valid"}
        assert validator.is_sabotage(result_valid) is False
        
        result_sabotage = {"validation_type": "sabotage"}
        assert validator.is_sabotage(result_sabotage) is True
        
        result_invalid = {"validation_type": "invalid"}
        assert validator.is_sabotage(result_invalid) is False

    @patch('rule_validator.requests.post')
    def test_get_applicable_rules_success(self, mock_post):
        """Test successful rule retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "rules": "PHB p.194: Attack action. PHB p.195: Damage rolls."
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        validator = RuleValidator()
        rules = validator.get_applicable_rules("attack action", n_results=5)

        assert "Attack action" in rules
        assert "Damage rolls" in rules
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://rule-agent:9002/retrieve_rules"
        assert call_args[1]["json"]["query"] == "attack action"
        assert call_args[1]["json"]["n_results"] == 5

    @patch('rule_validator.requests.post')
    def test_get_applicable_rules_error(self, mock_post):
        """Test rule retrieval error handling."""
        mock_post.side_effect = Exception("Database error")

        validator = RuleValidator()
        rules = validator.get_applicable_rules("attack", n_results=3)

        assert rules == ""

    @patch('rule_validator.requests.get')
    def test_check_health_success(self, mock_get):
        """Test health check when service is available."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        validator = RuleValidator()
        is_healthy = validator.check_health()

        assert is_healthy is True
        mock_get.assert_called_once_with(
            "http://rule-agent:9002/health",
            timeout=5
        )

    @patch('rule_validator.requests.get')
    def test_check_health_failure(self, mock_get):
        """Test health check when service is unavailable."""
        mock_get.side_effect = Exception("Connection failed")

        validator = RuleValidator()
        is_healthy = validator.check_health()

        assert is_healthy is False

    @patch('rule_validator.requests.get')
    def test_check_health_non_200(self, mock_get):
        """Test health check when service returns non-200."""
        mock_response = Mock()
        mock_response.status_code = 503
        mock_get.return_value = mock_response

        validator = RuleValidator()
        is_healthy = validator.check_health()

        assert is_healthy is False

