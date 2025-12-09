"""
Shared pytest fixtures for all tests.
"""

# Skip test files that import agent_tools due to types.Type.OBJECT import error
# This prevents the AttributeError during test collection
# These files import app.py or cli.py which import agent_tools.py
collect_ignore = [
    "unit/test_agent_tools.py",
    "unit/test_rule_agent_app.py",
    "unit/test_rule_agent_cli.py"
]

import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Add src directories to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src" / "backend"))
sys.path.insert(0, str(PROJECT_ROOT / "src" / "orchestrator"))
sys.path.insert(0, str(PROJECT_ROOT / "src" / "rule_agent"))

from api.utils.combat_engine import Character, CombatEngine


@pytest.fixture
def sample_player():
    """Create a sample player character for testing."""
    return Character(
        name="TestKnight",
        char_id=0,
        hp=20,
        ac=18,
        attributes={"STR": 4, "DEX": 2, "INT": 1},
        attack_bonus=7,
        damage=15,
        role="player"
    )


@pytest.fixture
def sample_enemy():
    """Create a sample enemy character for testing."""
    return Character(
        name="TestGoblin",
        char_id=0,
        hp=12,
        ac=13,
        attributes={"DEX": 3},
        attack_bonus=3,
        damage=6,
        role="enemy"
    )


@pytest.fixture
def sample_characters():
    """Create a set of test characters (players and enemies)."""
    players = [
        Character("Knight", 0, 20, 18, {"STR": 4, "DEX": 2}, 7, 15, "player"),
        Character("Wizard", 1, 14, 8, {"STR": 1, "DEX": 2, "INT": 5}, 3, 12, "player"),
    ]
    enemies = [
        Character("Goblin", 0, 12, 13, {"DEX": 3}, 3, 6, "enemy"),
        Character("Orc", 1, 15, 14, {"STR": 3, "DEX": 1}, 4, 8, "enemy"),
    ]
    return {"players": players, "enemies": enemies}


@pytest.fixture
def combat_engine(sample_characters):
    """Create an initialized combat engine for testing."""
    return CombatEngine(
        sample_characters["players"],
        sample_characters["enemies"]
    )


@pytest.fixture
def api_test_client():
    """Create FastAPI TestClient for Combat API."""
    import sys
    from pathlib import Path
    
    # Clear any existing 'service' module from cache
    modules_to_clear = ['service', 'api.service', 'api.routers.combat']
    for mod in modules_to_clear:
        if mod in sys.modules:
            del sys.modules[mod]
    
    backend_path = Path(__file__).parent.parent / "src" / "backend"
    sys.path.insert(0, str(backend_path))
    
    try:
        from api.service import app
        client = TestClient(app)
        return client
    finally:
        # Clean up path modifications if needed
        pass


@pytest.fixture
def sample_combat_request():
    """Sample combat initiation request data."""
    return {
        "players": [
            {
                "name": "TestKnight",
                "hp": 20,
                "ac": 18,
                "attributes": {"STR": 4, "DEX": 2},
                "attack_bonus": 7,
                "damage": 15,
                "role": "player"
            }
        ],
        "enemies": [
            {
                "name": "TestGoblin",
                "hp": 12,
                "ac": 13,
                "attributes": {"DEX": 3},
                "attack_bonus": 3,
                "damage": 6,
                "role": "enemy"
            }
        ]
    }

