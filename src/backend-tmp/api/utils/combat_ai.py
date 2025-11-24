"""
combat_ai.py
AI components for DnD combat: action parsing, enemy AI, and narrative generation.
Uses Google GenAI for LLM-based decision making and narration.
"""

import os
import random
import asyncio
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Optional
from google import genai
from google.genai import types

from api.utils.combat_engine import Character, CombatEngine, ACTION_REGISTRY
from api.utils.db_tool import retrieve_top_k

# Thread pool for running blocking GenAI calls
_genai_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="genai")


# ========== Action Parser for Players ==========
class ActionParser:
    """Parses natural language player input into structured actions using semantic search."""

    def __init__(self, engine: CombatEngine):
        self.engine = engine
        self.action_db_path = 'data/embeddings-actions.jsonl'
        self.enemy_db_path = 'data/embeddings-enemies.jsonl'

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
        try:
            action_id = retrieve_top_k(user_input, self.action_db_path, k=1)[0]
        except:
            # Fallback to melee attack if database not available
            action_id = 0

        action_type = ACTION_REGISTRY[action_id]

        # Find closest matching target among alive enemies
        alive_enemies = self.engine.state.get_alive(role="enemy")
        if not alive_enemies:
            return None

        try:
            enemy_ids = retrieve_top_k(user_input, self.enemy_db_path, k=100)
            # Match retrieved IDs with alive enemies
            target = None
            for enemy_id in enemy_ids:
                if any(e.id == enemy_id for e in alive_enemies):
                    target = self.engine.state.get_by_id(enemy_id, role="enemy")
                    break

            if not target:
                target = alive_enemies[0]  # Default to first alive enemy
        except:
            # Fallback to first alive enemy if database not available
            target = alive_enemies[0]

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
        self.action_db_path = 'data/embeddings-actions.jsonl'
        self.ally_db_path = 'data/embeddings-allies.jsonl'

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
        try:
            action_id = retrieve_top_k(action_text, self.action_db_path, k=1)[0]
        except:
            action_id = 0  # Default to melee attack

        action_type = ACTION_REGISTRY[action_id]

        # Find closest matching target among alive players
        alive_players = self.engine.state.get_alive(role="player")
        if not alive_players:
            return None

        try:
            ally_ids = retrieve_top_k(action_text, self.ally_db_path, k=100)
            # Match retrieved IDs with alive players
            target = None
            for ally_id in ally_ids:
                if any(p.id == ally_id for p in alive_players):
                    target = self.engine.state.get_by_id(ally_id, role="player")
                    break

            if not target:
                target = alive_players[0]  # Default to first alive player
        except:
            # Fallback to first alive player if database not available
            target = alive_players[0]

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
        # Initialize Google GenAI client using GCP credentials (if available)
        gcp_project = os.environ.get("GCP_PROJECT")
        gcp_location = os.environ.get("GCP_LOCATION", "us-central1")
        self.client = None
        self.use_llm = False
        try:
            if gcp_project:
                self.client = genai.Client(
                    vertexai=True,
                    project=gcp_project,
                    location=gcp_location
                )
                self.use_llm = True
            else:
                print("GCP_PROJECT not set, enemy bot will use simple attack strategy")
        except Exception as e:
            print(f"Failed to initialize GenAI client: {e}, using fallback strategy")
        self.parser = ActionParserBot(engine)

    def _call_genai_sync(self, prompt: str) -> Optional[str]:
        """Synchronous GenAI call (runs in thread pool)"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=150,
                    temperature=0.7,
                )
            )
            return response.text if response and response.text else None
        except Exception as e:
            print(f"GenAI call error: {e}")
            return None

    async def decide_action(self) -> Optional[dict]:
        """
        Generate enemy action using LLM tactical reasoning.
        Falls back to simple attack if LLM fails or times out.
        Uses async with timeout to prevent freezing.

        Returns:
            Action data dict or None if decision fails
        """
        actor = self.engine.current_actor
        if not actor:
            return None

        alive_players = self.engine.state.get_alive(role="player")
        if not alive_players:
            return None
        
        # Default fallback target
        target = random.choice(alive_players)
        
        # Try to use LLM for more interesting actions (only if client is available)
        if self.use_llm and self.client:
            try:
                # Construct tactical analysis prompt
                analysis_prompt = f"""
You are a DnD enemy bot controlling {actor.name}.

Current State:
- You are: {actor.name} (HP: {actor.hp}/{actor.max_hp}, AC: {actor.ac})
- Your allies: {[e.name for e in self.engine.state.enemies if e.alive]}
- Your enemies: {[p.name for p in self.engine.state.players if p.alive]}

Choose one hostile action and describe it in natural language.
Describe who you attack (or target) and how you perform it.
Stay consistent with D&D combat style and the character's role.
Keep your response concise (1-2 sentences).
Example: "I attack {target.name} with my weapon"
"""

                # Run GenAI call in thread pool with 5 second timeout
                loop = asyncio.get_event_loop()
                try:
                    action_text = await asyncio.wait_for(
                        loop.run_in_executor(_genai_executor, self._call_genai_sync, analysis_prompt),
                        timeout=5.0
                    )
                    
                    if action_text:
                        # Parse LLM output into structured action
                        action = self.parser.parse(actor, action_text)
                        if action:
                            return action
                except asyncio.TimeoutError:
                    print(f"GenAI call timed out after 5 seconds, using fallback")
                except Exception as e:
                    print(f"Error in async AI decision: {e}")
            except Exception as e:
                print(f"Error setting up AI decision (using fallback): {e}")
        
        # Fallback to simple attack (always works, never hangs)
        return {
            "id": 0,
            "type": "MeleeAttack",
            "target": target
        }


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

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=narrative_prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=200,
                    temperature=0.8,
                )
            )

            return response.text.strip()
        except Exception as e:
            print(f"Error in narration: {e}")
            # Fallback to basic narration
            return action_result
