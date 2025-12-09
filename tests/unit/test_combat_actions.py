"""
Unit tests for combat_engine.py action classes.
Tests MeleeAttack, RangedAttack, SpellAttack, Heal, and Flee actions.
"""

import pytest
from unittest.mock import Mock, patch
from api.utils.combat_engine import (
    Character, CombatEngine, MeleeAttack, RangedAttack, 
    SpellAttack, Heal, Flee
)


@pytest.mark.unit
class TestMeleeAttack:
    """Test MeleeAttack action."""

    def test_melee_attack_hit(self, sample_player, sample_enemy):
        """Test successful melee attack."""
        with patch('api.utils.combat_engine.random.randint') as mock_rand:
            mock_rand.side_effect = [15, 8]  # Attack roll: 15+7=22 (hits AC 13), Damage: 8
            
            engine = Mock()
            action = MeleeAttack(sample_player, sample_enemy)
            result = action.execute(engine)
            
            assert sample_enemy.hp < sample_enemy.max_hp
            assert "slashes" in result or "damage" in result

    def test_melee_attack_miss(self, sample_player, sample_enemy):
        """Test missed melee attack."""
        with patch('api.utils.combat_engine.random.randint') as mock_rand:
            mock_rand.return_value = 5  # Attack roll: 5+7=12 (misses AC 13)
            
            initial_hp = sample_enemy.hp
            engine = Mock()
            action = MeleeAttack(sample_player, sample_enemy)
            result = action.execute(engine)
            
            assert sample_enemy.hp == initial_hp
            assert "misses" in result or "miss" in result


@pytest.mark.unit
class TestRangedAttack:
    """Test RangedAttack action."""

    def test_ranged_attack_hit(self, sample_player, sample_enemy):
        """Test successful ranged attack."""
        with patch('api.utils.combat_engine.random.randint') as mock_rand:
            mock_rand.side_effect = [18, 6]  # Attack roll: 18+2=20 (hits), Damage: 6
            
            engine = Mock()
            action = RangedAttack(sample_player, sample_enemy)
            result = action.execute(engine)
            
            assert sample_enemy.hp < sample_enemy.max_hp
            assert "shoots" in result or "damage" in result

    def test_ranged_attack_miss(self, sample_player, sample_enemy):
        """Test missed ranged attack."""
        with patch('api.utils.combat_engine.random.randint') as mock_rand:
            mock_rand.return_value = 1  # Attack roll: 1+2=3 (misses)
            
            initial_hp = sample_enemy.hp
            engine = Mock()
            action = RangedAttack(sample_player, sample_enemy)
            result = action.execute(engine)
            
            assert sample_enemy.hp == initial_hp
            assert "misses" in result or "miss" in result


@pytest.mark.unit
class TestSpellAttack:
    """Test SpellAttack action."""

    def test_spell_attack_success(self, sample_player, sample_enemy):
        """Test successful spell attack (target fails save)."""
        sample_player.attributes["INT"] = 5
        sample_enemy.attributes["WIS"] = 1
        
        with patch('api.utils.combat_engine.random.randint') as mock_rand:
            # Save roll: 10+1=11, Spell DC: 10+5=15, so save fails
            mock_rand.side_effect = [10, 8]  # Save roll: 10, Damage: 8
            
            engine = Mock()
            action = SpellAttack(sample_player, sample_enemy, "Fireball")
            result = action.execute(engine)
            
            assert sample_enemy.hp < sample_enemy.max_hp
            assert "Fireball" in result or "scorches" in result

    def test_spell_attack_resisted(self, sample_player, sample_enemy):
        """Test spell attack where target resists (saves)."""
        sample_player.attributes["INT"] = 2
        sample_enemy.attributes["WIS"] = 10
        
        with patch('api.utils.combat_engine.random.randint') as mock_rand:
            # Save roll: 15+10=25, Spell DC: 10+2=12, so save succeeds
            mock_rand.return_value = 15
            
            initial_hp = sample_enemy.hp
            engine = Mock()
            action = SpellAttack(sample_player, sample_enemy, "Magic Missile")
            result = action.execute(engine)
            
            assert sample_enemy.hp == initial_hp
            assert "resists" in result


@pytest.mark.unit
class TestHeal:
    """Test Heal action."""

    def test_heal_action(self, sample_player, sample_enemy):
        """Test healing action."""
        sample_enemy.take_damage(10)
        initial_hp = sample_enemy.hp
        
        with patch('api.utils.combat_engine.random.randint') as mock_rand:
            mock_rand.return_value = 7  # Heal amount: 7+0=7
            
            engine = Mock()
            action = Heal(sample_player, sample_enemy)
            result = action.execute(engine)
            
            assert sample_enemy.hp > initial_hp
            assert "heals" in result

    def test_heal_caps_at_max_hp(self, sample_player):
        """Test healing cannot exceed max HP."""
        sample_player.take_damage(5)
        
        with patch('api.utils.combat_engine.random.randint') as mock_rand:
            mock_rand.return_value = 50  # Large heal amount
            
            engine = Mock()
            action = Heal(sample_player, sample_player)
            action.execute(engine)
            
            assert sample_player.hp == sample_player.max_hp


@pytest.mark.unit
class TestFlee:
    """Test Flee action."""

    def test_flee_action(self, sample_player):
        """Test flee action."""
        engine = Mock()
        action = Flee(sample_player)
        result = action.execute(engine)
        
        # Flee can either succeed or fail, so check for either outcome
        assert "flees" in result.lower() or "flee" in result.lower() or "blocked" in result.lower()


@pytest.mark.unit
class TestCombatEngineActions:
    """Test CombatEngine with various actions."""

    def test_engine_roll_initiative(self, sample_characters):
        """Test initiative rolling."""
        players = sample_characters["players"]
        enemies = sample_characters["enemies"]
        engine = CombatEngine(players, enemies)
        
        # Check that turn_queue is populated
        assert len(engine.turn_queue) > 0
        assert len(engine.turn_queue) == len(players) + len(enemies)

    def test_engine_next_turn_advances_queue(self, sample_characters):
        """Test next_turn advances through queue."""
        players = sample_characters["players"]
        enemies = sample_characters["enemies"]
        engine = CombatEngine(players, enemies)
        
        initial_queue_size = len(engine.turn_queue)
        actor1 = engine.next_turn()
        actor2 = engine.next_turn()
        
        assert actor1 != actor2 or initial_queue_size > 1
        assert len(engine.turn_queue) < initial_queue_size

    def test_engine_next_turn_new_round(self, sample_characters):
        """Test next_turn starts new round when queue empties."""
        players = sample_characters["players"]
        enemies = sample_characters["enemies"]
        engine = CombatEngine(players, enemies)
        
        initial_round = engine.round
        
        # Empty the queue
        while engine.turn_queue:
            engine.next_turn()
        
        # Next call should start new round
        engine.next_turn()
        assert engine.round > initial_round

    def test_engine_process_action(self, sample_characters):
        """Test processing action through dispatcher."""
        players = sample_characters["players"]
        enemies = sample_characters["enemies"]
        engine = CombatEngine(players, enemies)
        engine.current_actor = players[0]
        
        with patch('api.utils.combat_engine.random.randint') as mock_rand:
            mock_rand.side_effect = [15, 8]  # Hit and damage
            
            action_data = {
                "id": 0,  # MeleeAttack
                "target": enemies[0]
            }
            result = engine.process_action(action_data)
            
            assert isinstance(result, str)
            assert enemies[0].hp < enemies[0].max_hp

    def test_engine_remove_combatant(self, sample_characters):
        """Test removing combatant from battle."""
        players = sample_characters["players"]
        enemies = sample_characters["enemies"]
        engine = CombatEngine(players, enemies)
        
        initial_queue_size = len(engine.turn_queue)
        engine.remove_combatant(players[0])
        
        assert players[0].alive is False
        assert len(engine.turn_queue) < initial_queue_size or players[0] not in engine.turn_queue

    def test_action_dispatcher_resolve_action(self, sample_characters):
        """Test ActionDispatcher resolving actions."""
        players = sample_characters["players"]
        enemies = sample_characters["enemies"]
        engine = CombatEngine(players, enemies)
        dispatcher = engine.dispatcher
        
        with patch('api.utils.combat_engine.random.randint') as mock_rand:
            mock_rand.side_effect = [15, 8]
            
            action_data = {
                "id": 0,  # MeleeAttack
                "target": enemies[0]
            }
            result = dispatcher.resolve_action(players[0], action_data)
            
            assert isinstance(result, str)
            assert enemies[0].hp < enemies[0].max_hp

    def test_action_dispatcher_unknown_action(self, sample_characters):
        """Test ActionDispatcher with unknown action ID."""
        players = sample_characters["players"]
        enemies = sample_characters["enemies"]
        engine = CombatEngine(players, enemies)
        dispatcher = engine.dispatcher
        
        action_data = {
            "id": 999,  # Unknown action
            "target": enemies[0]
        }
        
        with pytest.raises(ValueError, match="Unknown action ID"):
            dispatcher.resolve_action(players[0], action_data)

    def test_flee_success(self, sample_player):
        """Test successful flee action."""
        engine = Mock()
        engine.remove_combatant = Mock()
        
        with patch('api.utils.combat_engine.random.random') as mock_random:
            mock_random.return_value = 0.7  # > 0.5, so flee succeeds
            
            action = Flee(sample_player)
            result = action.execute(engine)
            
            assert "flees" in result.lower() or "successfully" in result.lower()
            engine.remove_combatant.assert_called_once_with(sample_player)

    def test_flee_failure(self, sample_player):
        """Test failed flee action."""
        engine = Mock()
        
        with patch('api.utils.combat_engine.random.random') as mock_random:
            mock_random.return_value = 0.3  # < 0.5, so flee fails
            
            action = Flee(sample_player)
            result = action.execute(engine)
            
            assert "blocked" in result.lower() or "tries" in result.lower()

