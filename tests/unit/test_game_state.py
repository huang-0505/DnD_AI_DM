"""
Unit tests for orchestrator/game_state.py
Tests GameStateNode and GameStateTree classes.
"""

import pytest
import sys
from pathlib import Path

# Add orchestrator to path
ORCHESTRATOR_PATH = Path(__file__).parent.parent.parent / "src" / "orchestrator"
sys.path.insert(0, str(ORCHESTRATOR_PATH))

from game_state import GameStateNode, GameStateTree, GameStateType, AgentType


@pytest.mark.unit
class TestGameStateNode:
    """Test GameStateNode class functionality."""

    def test_node_initialization(self):
        """Test creating a node with proper attributes."""
        node = GameStateNode(
            state_type=GameStateType.NARRATION,
            agent=AgentType.NARRATOR
        )
        assert node.state_type == GameStateType.NARRATION
        assert node.agent == AgentType.NARRATOR
        assert node.parent_id is None
        assert node.id is not None
        assert len(node.children) == 0
        assert node.metadata == {}

    def test_node_with_parent(self):
        """Test creating a node with a parent."""
        parent = GameStateNode(
            state_type=GameStateType.NARRATION,
            agent=AgentType.NARRATOR
        )
        child = GameStateNode(
            state_type=GameStateType.COMBAT,
            agent=AgentType.COMBAT,
            parent_id=parent.id
        )
        assert child.parent_id == parent.id

    def test_node_with_metadata(self):
        """Test creating a node with metadata."""
        metadata = {"round": 1, "combat_count": 0}
        node = GameStateNode(
            state_type=GameStateType.COMBAT,
            agent=AgentType.COMBAT,
            metadata=metadata
        )
        assert node.metadata == metadata

    def test_node_to_dict(self):
        """Test converting node to dictionary."""
        node = GameStateNode(
            state_type=GameStateType.NARRATION,
            agent=AgentType.NARRATOR,
            metadata={"test": "value"}
        )
        node.narrative_text = "Test narrative"
        node.player_action = "I look around"
        node.agent_response = "You see a door"
        
        node_dict = node.to_dict()
        assert node_dict["state_type"] == "narration"
        assert node_dict["agent"] == "narrator"
        assert node_dict["metadata"]["test"] == "value"
        assert node_dict["narrative_text"] == "Test narrative"
        assert node_dict["player_action"] == "I look around"
        assert node_dict["agent_response"] == "You see a door"
        assert "id" in node_dict
        assert "created_at" in node_dict

    def test_node_rule_validation_tracking(self):
        """Test rule validation tracking fields."""
        node = GameStateNode(
            state_type=GameStateType.NARRATION,
            agent=AgentType.NARRATOR
        )
        assert node.rule_validation is None
        assert node.applicable_rules is None
        assert node.was_validated is False
        assert node.validation_errors == []


@pytest.mark.unit
class TestGameStateTree:
    """Test GameStateTree class functionality."""

    def test_tree_initialization(self):
        """Test creating an empty tree."""
        tree = GameStateTree()
        assert tree.root_id is None
        assert tree.current_node_id is None
        assert len(tree.nodes) == 0
        assert tree.narration_round == 0
        assert tree.combat_count == 0

    def test_create_root(self):
        """Test creating root node."""
        tree = GameStateTree()
        root = tree.create_root(GameStateType.NARRATION)
        
        assert root is not None
        assert tree.root_id == root.id
        assert tree.current_node_id == root.id
        assert root.id in tree.nodes
        assert root.state_type == GameStateType.NARRATION
        assert root.agent == AgentType.NARRATOR

    def test_add_child(self):
        """Test adding a child node."""
        tree = GameStateTree()
        root = tree.create_root(GameStateType.NARRATION)
        
        child = tree.add_child(
            parent_id=root.id,
            state_type=GameStateType.COMBAT,
            agent=AgentType.COMBAT
        )
        
        assert child is not None
        assert child.parent_id == root.id
        assert child.id in tree.nodes
        assert child.id in root.children

    def test_add_child_invalid_parent(self):
        """Test adding child with invalid parent raises error."""
        tree = GameStateTree()
        with pytest.raises(ValueError, match="Parent node.*not found"):
            tree.add_child(
                parent_id="invalid-id",
                state_type=GameStateType.COMBAT,
                agent=AgentType.COMBAT
            )

    def test_transition_to(self):
        """Test transitioning to a different node."""
        tree = GameStateTree()
        root = tree.create_root(GameStateType.NARRATION)
        child = tree.add_child(
            parent_id=root.id,
            state_type=GameStateType.COMBAT,
            agent=AgentType.COMBAT
        )
        
        tree.transition_to(child.id)
        assert tree.current_node_id == child.id

    def test_transition_to_invalid_node(self):
        """Test transitioning to invalid node raises error."""
        tree = GameStateTree()
        tree.create_root(GameStateType.NARRATION)
        
        with pytest.raises(ValueError, match="Node.*not found"):
            tree.transition_to("invalid-id")

    def test_get_current(self):
        """Test getting current node."""
        tree = GameStateTree()
        root = tree.create_root(GameStateType.NARRATION)
        
        current = tree.get_current()
        assert current is not None
        assert current.id == root.id

    def test_get_current_none(self):
        """Test getting current when no current node."""
        tree = GameStateTree()
        assert tree.get_current() is None

    def test_get_node(self):
        """Test getting a specific node by ID."""
        tree = GameStateTree()
        root = tree.create_root(GameStateType.NARRATION)
        
        node = tree.get_node(root.id)
        assert node is not None
        assert node.id == root.id

    def test_get_node_not_found(self):
        """Test getting non-existent node returns None."""
        tree = GameStateTree()
        assert tree.get_node("invalid-id") is None

    def test_get_path_from_root(self):
        """Test getting path from root to current node."""
        tree = GameStateTree()
        root = tree.create_root(GameStateType.NARRATION)
        child = tree.add_child(
            parent_id=root.id,
            state_type=GameStateType.COMBAT,
            agent=AgentType.COMBAT
        )
        tree.transition_to(child.id)
        
        path = tree.get_path_from_root()
        assert len(path) == 2
        assert path[0].id == root.id
        assert path[1].id == child.id

    def test_get_path_from_root_empty(self):
        """Test getting path when no current node."""
        tree = GameStateTree()
        path = tree.get_path_from_root()
        assert path == []

    def test_increment_narration_round(self):
        """Test incrementing narration round counter."""
        tree = GameStateTree()
        assert tree.narration_round == 0
        
        tree.increment_narration_round()
        assert tree.narration_round == 1
        
        tree.increment_narration_round()
        assert tree.narration_round == 2

    def test_increment_combat_count(self):
        """Test incrementing combat counter."""
        tree = GameStateTree()
        assert tree.combat_count == 0
        
        tree.increment_combat_count()
        assert tree.combat_count == 1
        
        tree.increment_combat_count()
        assert tree.combat_count == 2

    def test_should_trigger_combat(self):
        """Test combat trigger detection."""
        tree = GameStateTree()
        tree.combat_rounds = [3, 5, 10]
        
        tree.narration_round = 2
        assert tree.should_trigger_combat() is False
        
        tree.narration_round = 3
        assert tree.should_trigger_combat() is True
        
        tree.narration_round = 4
        assert tree.should_trigger_combat() is False
        
        tree.narration_round = 5
        assert tree.should_trigger_combat() is True

    def test_should_end_game(self):
        """Test game end detection."""
        tree = GameStateTree()
        tree.max_combats = 5
        
        tree.combat_count = 4
        assert tree.should_end_game() is False
        
        tree.combat_count = 5
        assert tree.should_end_game() is True
        
        tree.combat_count = 6
        assert tree.should_end_game() is True

    def test_to_dict(self):
        """Test converting tree to dictionary."""
        tree = GameStateTree()
        root = tree.create_root(GameStateType.NARRATION)
        child = tree.add_child(
            parent_id=root.id,
            state_type=GameStateType.COMBAT,
            agent=AgentType.COMBAT
        )
        
        tree_dict = tree.to_dict()
        assert "nodes" in tree_dict
        assert tree_dict["root_id"] == root.id
        assert tree_dict["current_node_id"] == root.id
        assert tree_dict["narration_round"] == 0
        assert tree_dict["combat_count"] == 0
        assert len(tree_dict["nodes"]) == 2

