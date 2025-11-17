# DnD Combat Frontend

Medieval-styled frontend for the DnD Combat Simulator.

## Features

- **DnD Medieval Art Style**: Parchment textures, medieval fonts, and thematic colors
- **Three-panel Layout**:
  - Left: Player characters with HP bars and stats
  - Center: Narrative dialogue panel showing AI-generated combat descriptions
  - Right: Enemy characters with HP bars and stats
- **Interactive Combat**: Text-based action input with natural language processing
- **Real-time Updates**: Character states update dynamically during battle

## Running the Frontend

### Using Docker (Recommended)

```bash
chmod +x docker-shell.sh
./docker-shell.sh
```

Inside the container:
```bash
http-server -p 8080
```

Then open your browser to `http://localhost:8080`

### Without Docker

Simply open `index.html` in a web browser, or use any static file server:

```bash
python -m http.server 8080
# or
npx http-server -p 8080
```

## Configuration

The frontend expects the backend API to be running at `http://localhost:9000`.

To change this, edit the `BASE_API_URL` constant in `main.js`.

## UI Components

- **Start Combat Button**: Initializes a new combat session
- **Action Input**: Enter natural language combat actions
- **Character Cards**: Display HP, AC, attack bonus, and damage
- **Narrative Panel**: Shows AI-generated combat narration
- **Round Counter**: Tracks current combat round

## Styling

The UI uses:
- **Fonts**: Cinzel (serif), MedievalSharp (display)
- **Color Scheme**: Parchment, ink, gold, blood-red, forest-green
- **Layout**: CSS Grid for responsive design
