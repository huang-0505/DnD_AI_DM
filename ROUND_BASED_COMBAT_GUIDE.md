# Round-Based Combat System Guide

## Overview

The game now uses a **fixed round-based combat system** where:
- Combat is triggered at specific narration rounds (default: rounds 3, 10, 15)
- The game ends after completing a certain number of combats (default: 5 combats)
- Choices are always displayed to prevent them from disappearing
- Round and combat count are displayed in the UI

## Features

### 1. Round-Based Combat Triggers

Combat is automatically available (and can be forced) at specific narration rounds. By default:
- **Round 3**: First combat opportunity
- **Round 10**: Second combat opportunity  
- **Round 15**: Third combat opportunity

You can customize these rounds when starting a game.

### 2. Combat Counter

The system tracks:
- **Narration Round**: Number of narration actions taken (increments each time player takes an action)
- **Combat Count**: Number of combats completed
- **Max Combats**: Maximum combats before game ends (default: 5)

### 3. Game Ending

The game automatically ends when:
- The combat count reaches the maximum (default: 5 combats)
- This happens after completing a combat encounter

### 4. Always-Available Choices

Choices are now always generated and displayed, even if the AI doesn't provide them. Default choices are provided as fallback.

## Configuration

### Starting a Game with Custom Settings

When calling the `/api/game/start` endpoint, you can customize:

```json
{
  "campaign_id": "example-campaign",
  "character_class": "Fighter",
  "character_name": "Aragorn",
  "max_combats": 5,           // Game ends after 5 combats (default: 5)
  "combat_rounds": [3, 10, 15]  // Combat available at these rounds (default: [3, 10, 15])
}
```

### Example: More Frequent Combat

```json
{
  "max_combats": 10,
  "combat_rounds": [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
}
```

### Example: Longer Game

```json
{
  "max_combats": 3,
  "combat_rounds": [5, 15, 25]
}
```

## How It Works

### Round Tracking

1. Each time a player takes a narration action, `narration_round` increments
2. The system checks if the current round is in `combat_rounds`
3. If yes, combat becomes available (the "⚔️ Enter Combat" button becomes active)

### Combat Triggering

Combat can be triggered in three ways:

1. **Round-Based (Automatic)**: At specific rounds, combat is forced after narration
2. **Player Request**: Player clicks "⚔️ Enter Combat" when available
3. **AI Detection**: The narrator detects combat in the narrative (fallback)

### Combat Completion

1. After combat ends, `combat_count` increments
2. The system checks if `combat_count >= max_combats`
3. If yes, the game ends with a victory message
4. If no, narration continues with choices

## UI Display

The frontend now shows:
- **Round: X** - Current narration round
- **Combats: X/Y** - Current combat count vs maximum
- **⚔️ Enter Combat** button (red when available, gray when not)
- Ending message when game completes

## Code Changes

### Backend (`src/orchestrator/`)

1. **`game_state.py`**:
   - Added `narration_round`, `combat_count`, `max_combats`, `combat_rounds` to `GameStateTree`
   - Added `increment_narration_round()`, `increment_combat_count()`, `should_trigger_combat()`, `should_end_game()` methods

2. **`app.py`**:
   - Modified `GameStartRequest` to accept `max_combats` and `combat_rounds`
   - Modified `handle_narration_action()` to:
     - Increment narration round
     - Check for round-based combat triggers
     - Check for game ending after max combats
   - Modified `handle_combat_action()` to:
     - Increment combat count after combat ends
     - Check for game ending
   - Modified `_get_choices_with_combat()` to check round-based triggers
   - Added fallback choices generation

### Frontend (`src/frontend/app/game/page.tsx`)

1. Updated `Message` interface to include:
   - `narrationRound`, `combatCount`, `maxCombats`
   - `isEnding`, `endingType`

2. Added UI elements to display:
   - Round and combat count
   - Ending messages
   - Always show choices (even if empty)

## Testing

To test the system:

1. Start a game with default settings
2. Take actions until round 3 - combat should become available
3. Enter combat and complete it
4. Continue until round 10 - combat available again
5. Complete 5 combats total - game should end

## Troubleshooting

### Choices Disappearing

- Fixed: Choices are now always generated, with fallback defaults if AI doesn't provide them
- Check: Ensure `response_choices` is being set in the response

### Combat Not Available

- Check: Is the current round in `combat_rounds`?
- Check: Is `combat_available` set correctly in story tree nodes?
- Check: Round counter is incrementing correctly

### Game Not Ending

- Check: Is `combat_count` incrementing after each combat?
- Check: Is `max_combats` set correctly?
- Check: Is `should_end_game()` being called after combat ends?

