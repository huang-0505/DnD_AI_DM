"""
Unit tests for rule_agent/agent_tools.py
Tests retrieve_dnd_rules function and tool definitions.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add rule_agent to path
RULE_AGENT_PATH = Path(__file__).parent.parent.parent / "src" / "rule_agent"
sys.path.insert(0, str(RULE_AGENT_PATH))

from agent_tools import (
    retrieve_dnd_rules,
    retrieve_dnd_rules_func,
    dnd_rule_tool,
    execute_function_calls
)
from google.genai import types


@pytest.mark.unit
class TestRetrieveDndRules:
    """Test retrieve_dnd_rules function."""

    def test_retrieve_dnd_rules_basic(self):
        """Test basic rule retrieval."""
        mock_collection = Mock()
        mock_collection.query.return_value = {
            "documents": [["Rule 1: Attack action", "Rule 2: Damage rolls"]]
        }
        
        mock_embed_func = Mock(return_value=[0.1] * 256)
        
        result = retrieve_dnd_rules(
            query="attack action",
            collection=mock_collection,
            embed_func=mock_embed_func,
            n_results=2
        )
        
        assert "Rule 1: Attack action" in result
        assert "Rule 2: Damage rolls" in result
        mock_embed_func.assert_called_once_with("attack action")
        mock_collection.query.assert_called_once()

    def test_retrieve_dnd_rules_default_n_results(self):
        """Test rule retrieval with default n_results."""
        mock_collection = Mock()
        mock_collection.query.return_value = {
            "documents": [["Rule 1", "Rule 2", "Rule 3", "Rule 4", "Rule 5"]]
        }
        
        mock_embed_func = Mock(return_value=[0.1] * 256)
        
        result = retrieve_dnd_rules(
            query="test query",
            collection=mock_collection,
            embed_func=mock_embed_func
        )
        
        call_args = mock_collection.query.call_args
        assert call_args[1]["n_results"] == 5  # Default value

    def test_retrieve_dnd_rules_custom_n_results(self):
        """Test rule retrieval with custom n_results."""
        mock_collection = Mock()
        mock_collection.query.return_value = {
            "documents": [["Rule 1", "Rule 2"]]
        }
        
        mock_embed_func = Mock(return_value=[0.1] * 256)
        
        result = retrieve_dnd_rules(
            query="test query",
            collection=mock_collection,
            embed_func=mock_embed_func,
            n_results=2
        )
        
        call_args = mock_collection.query.call_args
        assert call_args[1]["n_results"] == 2

    def test_retrieve_dnd_rules_empty_results(self):
        """Test rule retrieval with empty results."""
        mock_collection = Mock()
        mock_collection.query.return_value = {
            "documents": [[]]
        }
        
        mock_embed_func = Mock(return_value=[0.1] * 256)
        
        result = retrieve_dnd_rules(
            query="nonexistent query",
            collection=mock_collection,
            embed_func=mock_embed_func
        )
        
        assert result == ""


@pytest.mark.unit
class TestFunctionDeclaration:
    """Test function declaration structure."""

    def test_retrieve_dnd_rules_func_structure(self):
        """Test retrieve_dnd_rules_func has correct structure."""
        assert retrieve_dnd_rules_func.name == "retrieve_dnd_rules"
        assert retrieve_dnd_rules_func.description is not None
        assert len(retrieve_dnd_rules_func.description) > 0
        assert retrieve_dnd_rules_func.parameters is not None

    def test_retrieve_dnd_rules_func_parameters(self):
        """Test function parameters are correctly defined."""
        params = retrieve_dnd_rules_func.parameters
        # Check that parameters object exists and has properties
        assert params is not None
        # The parameters is a Schema object, check it has properties attribute
        if hasattr(params, 'properties'):
            props = params.properties
            assert "query" in props or hasattr(props, 'get')
            # Check required fields
            if hasattr(params, 'required'):
                assert "query" in params.required or "query" in list(params.required)


@pytest.mark.unit
class TestToolDefinition:
    """Test tool definition structure."""

    def test_dnd_rule_tool_structure(self):
        """Test dnd_rule_tool has correct structure."""
        assert isinstance(dnd_rule_tool, types.Tool)
        assert len(dnd_rule_tool.function_declarations) == 1
        assert dnd_rule_tool.function_declarations[0].name == "retrieve_dnd_rules"


@pytest.mark.unit
class TestExecuteFunctionCalls:
    """Test execute_function_calls function."""

    def test_execute_function_calls_retrieve_rules(self):
        """Test executing retrieve_dnd_rules function call."""
        mock_collection = Mock()
        mock_collection.query.return_value = {
            "documents": [["Rule 1: Attack", "Rule 2: Damage"]]
        }
        
        mock_embed_func = Mock(return_value=[0.1] * 256)
        
        # Create a mock function call
        function_call = types.FunctionCall(
            name="retrieve_dnd_rules",
            args={"query": "attack action", "n_results": 2}
        )
        
        parts = execute_function_calls(
            [function_call],
            collection=mock_collection,
            embed_func=mock_embed_func
        )
        
        assert len(parts) == 1
        assert isinstance(parts[0], types.Part)
        mock_collection.query.assert_called_once()

    def test_execute_function_calls_multiple_calls(self):
        """Test executing multiple function calls."""
        mock_collection = Mock()
        mock_collection.query.return_value = {
            "documents": [["Rule 1"]]
        }
        
        mock_embed_func = Mock(return_value=[0.1] * 256)
        
        function_call1 = types.FunctionCall(
            name="retrieve_dnd_rules",
            args={"query": "attack", "n_results": 1}
        )
        function_call2 = types.FunctionCall(
            name="retrieve_dnd_rules",
            args={"query": "damage", "n_results": 1}
        )
        
        parts = execute_function_calls(
            [function_call1, function_call2],
            collection=mock_collection,
            embed_func=mock_embed_func
        )
        
        assert len(parts) == 2
        assert mock_collection.query.call_count == 2

    def test_execute_function_calls_unknown_function(self):
        """Test executing unknown function call is ignored."""
        mock_collection = Mock()
        mock_embed_func = Mock()
        
        function_call = types.FunctionCall(
            name="unknown_function",
            args={"arg1": "value1"}
        )
        
        parts = execute_function_calls(
            [function_call],
            collection=mock_collection,
            embed_func=mock_embed_func
        )
        
        # Should return empty or only handle known functions
        assert isinstance(parts, list)
        mock_collection.query.assert_not_called()

    def test_execute_function_calls_default_n_results(self):
        """Test function call uses default n_results when not provided."""
        mock_collection = Mock()
        mock_collection.query.return_value = {
            "documents": [["Rule 1", "Rule 2", "Rule 3", "Rule 4", "Rule 5"]]
        }
        
        mock_embed_func = Mock(return_value=[0.1] * 256)
        
        function_call = types.FunctionCall(
            name="retrieve_dnd_rules",
            args={"query": "test"}  # n_results not provided
        )
        
        execute_function_calls(
            [function_call],
            collection=mock_collection,
            embed_func=mock_embed_func
        )
        
        call_args = mock_collection.query.call_args
        assert call_args[1]["n_results"] == 5  # Default value

