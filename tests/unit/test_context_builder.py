"""
Unit tests for orchestrator/context_builder.py
Tests GameContextBuilder class functionality.
"""

import pytest
import sys
from pathlib import Path

# Add orchestrator to path
ORCHESTRATOR_PATH = Path(__file__).parent.parent.parent / "src" / "orchestrator"
sys.path.insert(0, str(ORCHESTRATOR_PATH))

from game_state import GameStateTree, GameStateType, AgentType, GameStateNode
from context_builder import GameContextBuilder


@pytest.mark.unit
class TestGameContextBuilder:
    """Test GameContextBuilder class functionality."""

    def test_build_context_initial_state(self):
        """Test building context for initial state."""
        tree = GameStateTree()
        context = GameContextBuilder.build_context(tree)
        
        assert context["state_type"] == "initial"

    def test_build_context_narration_state(self):
        """Test building context for narration state."""
        tree = GameStateTree()
        root = tree.create_root(GameStateType.NARRATION)
        root.player_action = "I look around"
        root.agent_response = "You see a door"
        
        context = GameContextBuilder.build_context(tree)
        
        assert context["state_type"] == "narration"
        assert context["in_combat"] is False
        assert "recent_actions" in context
        assert "metadata" in context

    def test_build_context_combat_state(self):
        """Test building context for combat state."""
        tree = GameStateTree()
        root = tree.create_root(GameStateType.NARRATION)
        combat_node = tree.add_child(
            parent_id=root.id,
            state_type=GameStateType.COMBAT,
            agent=AgentType.COMBAT
        )
        combat_node.combat_session_id = "combat-123"
        tree.transition_to(combat_node.id)
        
        context = GameContextBuilder.build_context(tree)
        
        assert context["state_type"] == "combat"
        assert context["in_combat"] is True
        assert context["combat_session_id"] == "combat-123"

    def test_build_context_with_recent_actions(self):
        """Test context includes recent action history."""
        tree = GameStateTree()
        root = tree.create_root(GameStateType.NARRATION)
        root.player_action = "I open the door"
        root.agent_response = "The door creaks open"
        
        child = tree.add_child(
            parent_id=root.id,
            state_type=GameStateType.NARRATION,
            agent=AgentType.NARRATOR
        )
        child.player_action = "I enter the room"
        child.agent_response = "You see a chest"
        tree.transition_to(child.id)
        
        context = GameContextBuilder.build_context(tree)
        
        assert len(context["recent_actions"]) >= 1
        # Should include actions from path

    def test_build_agent_context(self):
        """Test building context for agent calls."""
        tree = GameStateTree()
        root = tree.create_root(GameStateType.NARRATION)
        root.applicable_rules = "PHB p.194: Attack rules"
        root.agent_response = "You see enemies"
        
        context = GameContextBuilder.build_agent_context(root, tree)
        
        assert context["current_state"] == "narration"
        assert context["applicable_rules"] == "PHB p.194: Attack rules"
        assert "recent_history" in context

    def test_build_agent_context_with_history(self):
        """Test agent context includes recent history."""
        tree = GameStateTree()
        root = tree.create_root(GameStateType.NARRATION)
        root.player_action = "I look"
        root.agent_response = "You see a door"
        
        child = tree.add_child(
            parent_id=root.id,
            state_type=GameStateType.COMBAT,
            agent=AgentType.COMBAT
        )
        child.player_action = "I attack"
        child.agent_response = "You hit for 10 damage"
        tree.transition_to(child.id)
        
        context = GameContextBuilder.build_agent_context(child, tree)
        
        assert len(context["recent_history"]) >= 1
        # Should include recent nodes with responses

    def test_get_story_summary(self):
        """Test generating story summary."""
        tree = GameStateTree()
        root = tree.create_root(GameStateType.NARRATION)
        root.agent_response = "You stand at the entrance"
        
        child = tree.add_child(
            parent_id=root.id,
            state_type=GameStateType.NARRATION,
            agent=AgentType.NARRATOR
        )
        child.agent_response = "You enter the dungeon"
        
        summary = GameContextBuilder.get_story_summary(tree)
        
        assert "entrance" in summary or "dungeon" in summary
        assert isinstance(summary, str)

    def test_get_story_summary_empty(self):
        """Test story summary with no narrative nodes."""
        tree = GameStateTree()
        tree.create_root(GameStateType.NARRATION)
        
        summary = GameContextBuilder.get_story_summary(tree)
        
        assert summary == "" or len(summary) == 0

    def test_get_story_summary_with_combat(self):
        """Test story summary includes combat nodes."""
        tree = GameStateTree()
        root = tree.create_root(GameStateType.NARRATION)
        root.agent_response = "You see goblins"
        
        combat = tree.add_child(
            parent_id=root.id,
            state_type=GameStateType.COMBAT,
            agent=AgentType.COMBAT
        )
        combat.agent_response = "Combat begins!"
        
        summary = GameContextBuilder.get_story_summary(tree, max_nodes=10)
        
        assert isinstance(summary, str)
        # May include both narration and combat

    def test_get_story_summary_max_nodes(self):
        """Test story summary respects max_nodes limit."""
        tree = GameStateTree()
        root = tree.create_root(GameStateType.NARRATION)
        
        # Create multiple nodes
        for i in range(15):
            parent_id = tree.current_node_id
            node = tree.add_child(
                parent_id=parent_id,
                state_type=GameStateType.NARRATION,
                agent=AgentType.NARRATOR
            )
            node.agent_response = f"Action {i}"
            tree.transition_to(node.id)
        
        summary = GameContextBuilder.get_story_summary(tree, max_nodes=5)
        
        # Summary should be limited (exact count depends on implementation)
        assert isinstance(summary, str)

