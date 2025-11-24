# Story Tree JSON Format

This directory contains JSON files that define predefined story trees for campaigns. These trees ensure that stories progress toward specific endings and don't go on indefinitely.

## File Structure

Each story tree JSON file should be named `{campaign_id}.json` and placed in this directory.

## JSON Schema

```json
{
  "campaign_id": "string",           // Must match the campaign ID
  "root_node_id": "string",          // ID of the starting node
  "nodes": [
    {
      "node_id": "string",           // Unique identifier for this node
      "narrative": "string",         // The story text displayed to the player
      "choices": ["string"],         // Array of choice options (empty for endings)
      "is_ending": boolean,          // true if this is an ending node
      "ending_type": "string",       // Optional: "victory", "defeat", "neutral"
      "children": {                  // Maps choice text to child node IDs
        "choice text": "child_node_id"
      },
      "metadata": {                  // Optional metadata
        "location": "string",
        "encounter_type": "string",
        "difficulty": "string"
      }
    }
  ]
}
```

## Example

See `example-campaign.json` for a complete example.

## Key Features

1. **Guaranteed Endings**: Every story tree must have at least one ending node (`is_ending: true`)
2. **Choice Mapping**: The `children` object maps player choice text to the next node
3. **Fuzzy Matching**: The system will try to match player input to choices even if not exact
4. **Fallback to AI**: If no matching node is found, the system falls back to AI-generated narrative

## Creating a Story Tree

1. **Start with the root node**: This is where the story begins
2. **Define branches**: Each choice leads to a child node
3. **Ensure endings**: Every path should eventually lead to an ending node
4. **Add metadata**: Use metadata to track locations, encounter types, etc.

## Tips

- Keep choice text concise and clear
- Use descriptive node IDs (e.g., "dragon_lair_1", "puzzle_room_2")
- Include multiple ending types for variety (victory, defeat, neutral)
- Test your tree to ensure all paths lead to endings
- Use metadata to help guide the AI when falling back

## Integration

When a campaign starts:
1. The system looks for `{campaign_id}.json` in this directory
2. If found, the story tree is loaded and used to guide the narrative
3. Player choices are matched against the tree's choice mappings
4. When an ending node is reached, the game ends

If no story tree is found, the game runs in free-form mode with AI-generated narratives.

