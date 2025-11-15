# DnD Combat Simulator - Project Refactor Summary

## Overview

This document describes the newly created `backend-tmp/` and `frontend-tmp/` directories, which implement a clean, modern DnD combat simulator following the architectural patterns of the existing `api-service` and `frontend-simple` directories.

## ✅ What Was Created

### 📁 Backend (`src/backend-tmp/`)

A FastAPI-based backend service that integrates the combat agent with AI-powered features.

#### Structure
```
backend-tmp/
├── api/
│   ├── service.py              # Main FastAPI app with CORS
│   ├── routers/
│   │   └── combat.py           # Combat API endpoints
│   └── utils/
│       ├── combat_engine.py    # Turn-based combat logic
│       ├── combat_ai.py        # AI narrator & enemy bot
│       └── db_tool.py          # Embedding utilities
├── Dockerfile                  # Python 3.12 + uv
├── pyproject.toml              # Dependencies
├── docker-entrypoint.sh        # Container entrypoint
├── docker-shell.sh             # Dev environment setup
├── .gitignore
└── README.md
```

#### Key Features
- **Combat Engine**: Turn-based D&D combat with initiative, HP tracking, actions
- **AI Enemy Decisions**: Uses Google Gemini to make tactical enemy choices
- **AI Narration**: Generates dramatic, D&D-style combat narratives
- **RESTful API**: Clean session-based endpoints
- **Action Parsing**: Natural language understanding for player actions

#### API Endpoints
- `POST /combat/start` - Initialize combat session
- `GET /combat/state/{session_id}` - Get current state
- `POST /combat/action/{session_id}` - Submit player action
- `DELETE /combat/session/{session_id}` - End combat

---

### 🎨 Frontend (`src/frontend-tmp/`)

A medieval-styled web interface with a three-panel layout.

#### Structure
```
frontend-tmp/
├── index.html                  # Main HTML
├── style.css                   # DnD medieval styling
├── main.js                     # Combat app logic
├── Dockerfile                  # Node.js + http-server
├── docker-shell.sh             # Dev environment
├── .gitignore
└── README.md
```

#### Key Features
- **Medieval Art Style**: Parchment textures, medieval fonts (Cinzel, MedievalSharp)
- **Three-Panel Layout**:
  - **Left**: Player characters with HP bars
  - **Center**: Narrative dialogue panel
  - **Right**: Enemy characters with HP bars
- **Bottom**: Action input box for player commands
- **Real-time Updates**: Dynamic character state updates
- **Responsive Design**: Adapts to different screen sizes

#### UI Components
- Character cards with HP bars, stats (AC, ATK, DMG)
- Animated narrative entries
- Turn indicator showing current actor
- Round counter
- Battle result screen

---

## 🎯 Design Principles Followed

### From `api-service`
✅ FastAPI with CORS middleware
✅ Router-based endpoint organization
✅ Pydantic models for request/response validation
✅ Docker containerization with uv package manager
✅ Separation of concerns (routers vs utils)
✅ Environment variable configuration
✅ Development vs production modes

### From `frontend-simple`
✅ Simple HTML/CSS/JS structure (no build process)
✅ Axios for API calls
✅ Clean CSS variables for theming
✅ Responsive design
✅ Docker deployment with http-server
✅ Session-based state management

---

## 🚀 How to Run

### Backend

```bash
cd src/backend-tmp
chmod +x docker-shell.sh
./docker-shell.sh
```

Inside container:
```bash
uvicorn_server
```

Backend runs at `http://localhost:9000`

### Frontend

```bash
cd src/frontend-tmp
chmod +x docker-shell.sh
./docker-shell.sh
```

Inside container:
```bash
http-server -p 8080
```

Frontend runs at `http://localhost:8080`

---

## 🔧 Configuration

### Backend Environment Variables
- `GCP_PROJECT` - Your GCP project ID
- `GCP_LOCATION` - GCP region (default: us-central1)
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to service account key

### Frontend Configuration
Edit `BASE_API_URL` in `main.js` to change backend endpoint.

---

## 🎮 User Flow

1. User opens frontend → Sees welcome screen
2. Clicks "Start Combat" → Backend creates session with preset characters
3. Backend rolls initiative → Determines turn order
4. **Player Turn**:
   - User types action: "I attack the goblin with my sword"
   - Frontend sends to backend
   - Backend parses action, executes combat logic
   - AI generates dramatic narrative
   - Returns updated state
5. **Enemy Turn**:
   - Backend AI decides enemy action
   - Executes combat logic
   - AI generates narrative
   - Returns updated state
6. Repeat until one side is defeated
7. Display victory/defeat message

---

## 🆕 What's New vs Original Combat Agent

### Architecture Improvements
- **API-first design**: RESTful endpoints instead of CLI
- **Session management**: Multiple concurrent battles
- **Stateless backend**: Session data in memory (can be moved to Redis/DB)
- **Web UI**: Accessible interface vs command-line

### Features Added
- **AI Narrator**: Generates vivid combat descriptions
- **Visual feedback**: HP bars, character status, turn indicators
- **Automatic enemy turns**: Seamless player/enemy flow
- **Medieval theming**: Immersive D&D aesthetic

### Code Organization
- **Modular routers**: Easy to add new endpoints
- **Pydantic validation**: Type-safe API contracts
- **Clean separation**: Engine, AI, and API layers

---

## 📊 Technology Stack

### Backend
- Python 3.12
- FastAPI (web framework)
- Google GenAI (Vertex AI for LLM)
- Pydantic (data validation)
- NumPy/Pandas (embeddings, optional)
- Uvicorn (ASGI server)
- Docker + uv (containerization)

### Frontend
- Vanilla HTML/CSS/JavaScript
- Axios (HTTP client)
- Google Fonts (Cinzel, MedievalSharp)
- CSS Grid (layout)
- Docker + http-server

---

## 🔮 Future Enhancements

### Backend
- [ ] Redis for session persistence
- [ ] Database for combat history
- [ ] Multiplayer support (multiple players)
- [ ] Custom character creation endpoint
- [ ] Spell/ability system expansion
- [ ] Status effects (poison, stun, etc.)

### Frontend
- [ ] Character portraits/images
- [ ] Sound effects and music
- [ ] Combat log export
- [ ] Mobile-optimized layout
- [ ] Dark/light theme toggle
- [ ] Animation effects for attacks

---

## 📝 Notes

- **No Legacy Logic**: All code is new, only architectural patterns are borrowed
- **Self-Contained**: Both services run independently with Docker
- **Clean Dependencies**: Minimal, production-ready package lists
- **Follows Best Practices**: Modern Python/JS patterns, security, error handling

---

## 📚 Related Documentation

- [Backend README](src/backend-tmp/README.md)
- [Frontend README](src/frontend-tmp/README.md)
- [Original Combat Agent](src/combat_agent_refactored/)

---

**Created**: 2025-11-15
**Pattern Source**: `api-service` + `frontend-simple`
**Purpose**: Clean DnD combat simulator with AI-powered narration
