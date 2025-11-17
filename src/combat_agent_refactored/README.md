# 🎲 DnD Combat Simulator

A turn-based DnD-style combat simulator with AI-powered enemies using semantic search and LLM reasoning.

## 📁 Project Structure

```
tutorial/
├── secrets/                    # GCP credentials (shared, not tracked)
│   └── dnd-master.json
│
└── dnd_master/src/combat_agent_refactored/
    │
    ├── input/                      # Input JSON data files
    │   ├── actions.json           # Available combat actions
    │   ├── allies.json            # Player character definitions
    │   └── enemies.json           # Enemy character definitions
    │
    ├── output/                     # Generated embedding databases
    │   ├── embeddings-actions.jsonl
    │   ├── embeddings-allies.jsonl
    │   └── embeddings-enemies.jsonl
    │
    ├── combat_engine.py           # Core combat logic and rules
    ├── db_tool.py                 # Embedding generation and retrieval
    ├── cli.py                     # Command-line interface
    │
    ├── Dockerfile                 # Container definition
    ├── docker-shell.sh            # Build and run container
    ├── docker-entrypoint.sh       # Container entry point
    └── pyproject.toml             # Python dependencies
```

## 🚀 Quick Start

### 1. Using Docker (Recommended)

```bash
# Make scripts executable
chmod +x docker-shell.sh docker-entrypoint.sh

# Build and run container
./docker-shell.sh

# Inside container: Initialize databases
python cli.py --init-db

# Start combat simulation
python cli.py
```

### 2. Local Setup

```bash
# Install dependencies
pip install -e .

# Set environment variables
export GCP_PROJECT="your-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="./secrets/dnd-master.json"
export OPENAI_API_KEY="your-openai-key"

# Initialize databases
python cli.py --init-db

# Run simulation
python cli.py
```

## 🎮 Usage

### Combat Simulation

```bash
# Run with AI enemies (default)
python cli.py

# Run without AI (random actions)
python cli.py --no-ai

# Use different OpenAI model
python cli.py --model gpt-4-turbo
```

### Database Management

```bash
# Generate embeddings for actions
python db_tool.py embed --input input/actions.json --output output/embeddings-actions.jsonl

# Query embeddings
python db_tool.py retrieve --query "attack the goblin" --file output/embeddings-actions.jsonl --k 5
```

## 🧩 Architecture

### Combat Engine (`combat_engine.py`)
- **Character**: Combatant state with HP, AC, attributes
- **BattleState**: Tracks all combatants and provides queries
- **Action**: Abstract base for combat actions (attack, spell, heal, flee)
- **ActionDispatcher**: Resolves action IDs to execution
- **CombatEngine**: Orchestrates turn order, initiative, and battle flow

### Database Tool (`db_tool.py`)
- **EmbeddingGenerator**: Creates text embeddings using Google GenAI
- **DatabaseManager**: Manages embedding databases (JSONL format)
- **cosine_similarity**: Semantic search for actions and targets

### CLI (`cli.py`)
- **ActionParser**: Parses player input using semantic search
- **ActionParserBot**: Parses AI decisions into actions
- **DnDBot**: LLM-powered enemy AI with tactical reasoning
- **Game Loop**: Manages player/enemy turns and combat flow

## 🔧 Configuration

### Environment Variables
```bash
GCP_PROJECT                     # Google Cloud project ID (required)
GCP_LOCATION                    # GCP region (default: us-central1)
GOOGLE_APPLICATION_CREDENTIALS  # Path to GCP service account JSON (required)
OPENAI_API_KEY                  # OpenAI API key for enemy AI (required)
```

### Input Data Format

**actions.json**:
```json
[
  {
    "id": 0,
    "name": "MeleeAttack",
    "description": "A forceful close-range strike...",
    "examples": ["attack goblin", "slash orc"]
  }
]
```

**allies.json / enemies.json**:
```json
[
  {
    "id": 0,
    "name": "Knight",
    "description": "A heavily armored warrior...",
    "role": "tank"
  }
]
```

## 📊 Features

- ✅ Turn-based combat with initiative rolls
- ✅ Multiple action types (melee, ranged, spell, heal, flee)
- ✅ Semantic search for natural language input
- ✅ LLM-powered enemy AI with tactical reasoning
- ✅ Modular architecture with clear separation of concerns
- ✅ Docker containerization for easy deployment
- ✅ Extensible action and character system

## 🛠️ Development

### Adding New Actions
1. Define action class in `combat_engine.py` inheriting from `Action`
2. Add to `ACTION_REGISTRY`
3. Update `input/actions.json` with description and examples
4. Regenerate embeddings: `python cli.py --init-db`

### Adding New Characters
1. Update `input/allies.json` or `input/enemies.json`
2. Modify `create_default_party()` or `create_default_enemies()` in `cli.py`
3. Regenerate embeddings if needed

## 📝 License

MIT License - Feel free to use and modify for your projects!
