"""
cli.py
Command-line interface to initialize and run DnD combat simulations.
Handles player input, enemy AI decisions, and game loop orchestration.
"""

import os
import random
import argparse
from typing import List, Optional
from google import genai
from google.genai import types

from combat_engine import Character, CombatEngine, ACTION_REGISTRY
from db_tool import retrieve_top_k


# ========== Action Parser for Players ==========
class ActionParser:
    """Parses natural language player input into structured actions using semantic search."""

    def __init__(self, engine: CombatEngine):
        self.engine = engine
        self.action_db_path = 'output/embeddings-actions.jsonl'
        self.enemy_db_path = 'output/embeddings-enemies.jsonl'

    def parse(self, actor: Character, user_input: str) -> Optional[dict]:
        """
        Parse player input into action data.

        Args:
            actor: The acting character
            user_input: Natural language action description

        Returns:
            Dict with action_id, type, and target, or None if parsing fails
        """
        # Find closest matching action
        action_id = retrieve_top_k(user_input, self.action_db_path, k=1)[0]
        action_type = ACTION_REGISTRY[action_id]

        # Find closest matching target among alive enemies
        alive_enemies = self.engine.state.get_alive(role="enemy")
        if not alive_enemies:
            print("❌ No enemies remaining!")
            return None

        enemy_ids = retrieve_top_k(user_input, self.enemy_db_path, k=100)

        # Match retrieved IDs with alive enemies
        target = None
        for enemy_id in enemy_ids:
            if any(e.id == enemy_id for e in alive_enemies):
                target = self.engine.state.get_by_id(enemy_id, role="enemy")
                break

        if not target:
            print(f"❌ Target not found or already defeated.")
            return None

        return {
            "id": action_id,
            "type": action_type,
            "target": target
        }


# ========== Action Parser for Enemy AI ==========
class ActionParserBot:
    """Parses enemy AI decisions into structured actions."""

    def __init__(self, engine: CombatEngine):
        self.engine = engine
        self.action_db_path = 'output/embeddings-actions.jsonl'
        self.ally_db_path = 'output/embeddings-allies.jsonl'

    def parse(self, actor: Character, action_text: str) -> Optional[dict]:
        """
        Parse bot-generated action description into action data.

        Args:
            actor: The acting enemy character
            action_text: LLM-generated action description

        Returns:
            Dict with action_id, type, and target, or None if parsing fails
        """
        # Find closest matching action
        action_id = retrieve_top_k(action_text, self.action_db_path, k=1)[0]
        action_type = ACTION_REGISTRY[action_id]

        # Find closest matching target among alive players
        alive_players = self.engine.state.get_alive(role="player")
        if not alive_players:
            print("❌ No players remaining!")
            return None

        ally_ids = retrieve_top_k(action_text, self.ally_db_path, k=100)

        # Match retrieved IDs with alive players
        target = None
        for ally_id in ally_ids:
            if any(p.id == ally_id for p in alive_players):
                target = self.engine.state.get_by_id(ally_id, role="player")
                break

        if not target:
            print(f"❌ Target not found or already defeated.")
            return None

        return {
            "id": action_id,
            "type": action_type,
            "target": target
        }


# ========== Enemy AI Agent ==========
class DnDBot:
    """AI agent for controlling enemy actions using LLM reasoning."""

    def __init__(self, engine: CombatEngine, model: str = "gemini-2.0-flash-001"):
        self.engine = engine
        self.model = model
        # Initialize Google GenAI client using GCP credentials
        gcp_project = os.environ.get("GCP_PROJECT")
        gcp_location = os.environ.get("GCP_LOCATION", "us-central1")
        self.client = genai.Client(
            vertexai=True,
            project=gcp_project,
            location=gcp_location
        )
        self.parser = ActionParserBot(engine)

    def decide_action(self) -> Optional[dict]:
        """
        Generate enemy action using LLM tactical reasoning.

        Returns:
            Action data dict or None if decision fails
        """
        actor = self.engine.current_actor

        # Construct tactical analysis prompt
        analysis_prompt = f"""
You are a DnD enemy bot controlling {actor.name}.

Current State:
- You are: {actor}
- Your allies: {self.engine.state.enemies}
- Your enemies: {self.engine.state.players}

Choose one hostile action and describe it in natural language.
Describe who you attack (or target) and how you perform it.
Stay consistent with D&D combat style and the character's role.
Keep your response concise (1-2 sentences).
"""

        print(f"\n🤖 {actor.name} is deciding action...")

        # Call Google GenAI
        response = self.client.models.generate_content(
            model=self.model,
            contents=analysis_prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=150,
                temperature=0.7,
            )
        )

        action_text = response.text
        print(f"🤖 {actor.name} decided: {action_text}")

        # Parse LLM output into structured action
        action = self.parser.parse(actor, action_text)
        return action

class DnDNarrator:
    """AI narrator for generating vivid combat descriptions"""

    def __init__(self, model: str = "gemini-2.0-flash-001"):
        self.model = model
        gcp_project = os.environ.get("GCP_PROJECT")
        gcp_location = os.environ.get("GCP_LOCATION", "us-central1")
        self.client = genai.Client(
            vertexai=True,
            project=gcp_project,
            location=gcp_location
        )

    def narrate(self, user_query: str, action_result: str) -> str:
        """
        Generate vivid narrative combining player intent and mechanical result.

        Args:
            user_query: Player's action description
            action_result: Mechanical outcome from engine

        Returns:
            Dramatic narrative description
        """
        narrative_prompt = f"""
You are a DnD Narrator describing an epic battle scene.

Player's Intent: "{user_query}"
Actual Result: "{action_result}"

Create a vivid, dramatic description (2-3 sentences) that:
- Describes the action cinematically
- Incorporates the player's intended action style
- Shows the actual mechanical outcome
- Uses D&D-style evocative language

IMPORTANT: When user_query and action_result conflict, prioritize the PLAYER'S INTENT in your narrative style while still showing the actual outcome.

Be dramatic and immersive. Make it feel epic!
"""

        response = self.client.models.generate_content(
            model=self.model,
            contents=narrative_prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=200,
                temperature=0.8,
            )
        )

        return response.text.strip()

# ========== Game Setup Functions ==========
def create_default_party() -> List[Character]:
    """Create default player party."""
    return [
        Character("Knight", 0, 20, 24, {"STR": 4, "DEX": 2, "INT": 1}, attack_bonus=7, damage=15),
        Character("Wizard", 1, 14, 8, {"STR": 1, "DEX": 2, "INT": 5}, attack_bonus=3, damage=12),
        Character("Ranger", 2, 16, 10, {"STR": 3, "DEX": 4, "INT": 2}, attack_bonus=6, damage=10),
        Character("Cleric", 3, 15, 10, {"STR": 2, "DEX": 2, "INT": 4}, attack_bonus=4, damage=8),
        Character("Barbarian", 4, 26, 18, {"STR": 5, "DEX": 3, "INT": 1}, attack_bonus=8, damage=18)
    ]


def create_default_enemies() -> List[Character]:
    """Create default enemy group."""
    return [
        Character("Goblin", 0, 12, 13, {"DEX": 3}, attack_bonus=3, damage=6, role="enemy"),
        Character("Troll", 3, 16, 13, {"STR": 4, "DEX": 2}, attack_bonus=5, damage=8, role="enemy"),
        Character("Dragon", 4, 20, 20, {"STR": 6, "DEX": 6, "INT": 6}, attack_bonus=8, damage=12, role="enemy")
    ]


# ========== Main Game Loop ==========
def run_combat_simulation(use_ai: bool = True, model: str = "gemini-2.0-flash-001"):
    """
    Run the main combat simulation loop.

    Args:
        use_ai: Whether to use LLM for enemy decisions (otherwise random)
        model: Google GenAI model to use for enemy AI (default: gemini-2.0-flash-001)
    """
    print("\n" + "="*60)
    print("⚔️  DnD COMBAT SIMULATOR")
    print("="*60)

    # Initialize combatants
    players = create_default_party()
    enemies = create_default_enemies()

    # Create combat engine
    engine = CombatEngine(players, enemies)

    # Create action parsers
    player_parser = ActionParser(engine)
    enemy_agent = DnDBot(engine, model=model) if use_ai else None
    narrator = DnDNarrator(model=model)

    print("\n⚔️ Battle Start!")
    engine.state.print_status()

    # Main combat loop
    while not engine.is_battle_over():
        actor = engine.next_turn()

        # Skip dead characters
        if not actor.alive:
            continue

        print(f"\n{'='*60}")
        print(f"🎯 {actor.name}'s Turn")
        print(f"{'='*60}")

        if actor.role == "player":
            # Player input
            while True:
                user_input = input(f"\n💬 {actor.name}, enter your action: ").strip()
                if not user_input:
                    print("⚠️ Please enter an action!")
                    continue

                action = player_parser.parse(actor, user_input)
                if action:
                    break

            script = engine.process_action(action)
            # Generate narrative
            narrative = narrator.narrate(user_input, script)
            print(f"\n📜 Narrative:\n{narrative}")

        else:
            # Enemy AI or random action
            if enemy_agent:
                action = enemy_agent.decide_action()
            else:
                # Fallback: random attack
                target = random.choice(engine.state.get_alive("player"))
                action = {"id": 0, "type": "MeleeAttack", "target": target}
                print(f"🤖 {actor.name} attacks {target.name}!")

            if action:
                script = engine.process_action(action)
                narrative = narrator.narrate(script, script)
                print(f"\n📜 Narrative:\n{narrative}")


                

    # Battle conclusion
    print("\n" + "="*60)
    print("✅ BATTLE OVER!")
    print("="*60)

    if any(p.alive for p in engine.state.players):
        print("\n🎉 Victory! The players have won!")
    else:
        print("\n💀 Defeat! The enemies have prevailed.")


# ========== CLI Entry Point ==========
def main():
    """CLI entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="DnD Combat Simulator - Run turn-based battles with AI enemies"
    )

    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Disable AI for enemy decisions (use random actions)"
    )

    parser.add_argument(
        "--model",
        type=str,
        default="gemini-2.0-flash-001",
        help="Google GenAI model for enemy AI (default: gemini-2.0-flash-001)"
    )

    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Initialize embedding databases before starting combat"
    )

    args = parser.parse_args()

    # Initialize databases if requested
    if args.init_db:
        print("\n📦 Initializing databases...")
        from db_tool import DatabaseManager, DBConfig

        config = DBConfig()
        db_manager = DatabaseManager(config)

        # Generate embeddings for all databases
        db_manager.create_database("input/actions.json", "output/embeddings-actions.jsonl")
        db_manager.create_database("input/allies.json", "output/embeddings-allies.jsonl")
        db_manager.create_database("input/enemies.json", "output/embeddings-enemies.jsonl")

        print("✅ Databases initialized!\n")

    # Run combat simulation
    run_combat_simulation(use_ai=not args.no_ai, model=args.model)


if __name__ == "__main__":
    main()
