# Story Tree System Guide

## Overview

The Story Tree System allows you to create **predefined story structures** stored in JSON files. This ensures:
- ✅ Stories progress toward **guaranteed endings**
- ✅ You control the narrative flow
- ✅ Players can still type custom actions (with AI fallback)
- ✅ Tree structure is preserved and trackable

## How It Works

1. **JSON Files**: Story trees are stored as JSON files in `src/orchestrator/story_trees/`
2. **Automatic Loading**: When a campaign starts, the system looks for `{campaign_id}.json`
3. **Choice Matching**: Player choices are matched against predefined nodes
4. **AI Fallback**: If no match is found, the system uses AI-generated narrative
5. **Ending Detection**: When an ending node is reached, the game ends

## Creating a Story Tree

### Step 1: Create JSON File

Create a file named `{campaign_id}.json` in `src/orchestrator/story_trees/`

Example: For campaign `"stormwreck-isle"`, create `stormwreck-isle.json`

### Step 2: Define Structure

```json
{
  "campaign_id": "stormwreck-isle",
  "root_node_id": "start_1",
  "nodes": [
    {
      "node_id": "start_1",
      "narrative": "You stand at the entrance...",
      "choices": ["Go left", "Go right", "Investigate"],
      "is_ending": false,
      "children": {
        "Go left": "left_path_1",
        "Go right": "right_path_1",
        "Investigate": "investigate_1"
      }
    },
    {
      "node_id": "left_path_1",
      "narrative": "You follow the left path...",
      "choices": ["Fight", "Sneak", "Retreat"],
      "is_ending": false,
      "children": {
        "Fight": "ending_victory",
        "Sneak": "ending_neutral",
        "Retreat": "start_1"
      }
    },
    {
      "node_id": "ending_victory",
      "narrative": "🎉 Victory! You have completed the adventure!",
      "choices": [],
      "is_ending": true,
      "ending_type": "victory"
    }
  ]
}
```

### Step 3: Key Requirements

- **Root Node**: Must have a `root_node_id` that matches a node's `node_id`
- **Endings**: At least one node must have `"is_ending": true`
- **Choice Mapping**: Each choice in `choices` should map to a child node in `children`
- **All Paths Lead to Endings**: Ensure every branch eventually reaches an ending

## Node Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `node_id` | string | ✅ | Unique identifier |
| `narrative` | string | ✅ | Story text shown to player |
| `choices` | string[] | ✅ | Array of choice options (empty for endings) |
| `is_ending` | boolean | ✅ | `true` if this ends the game |
| `ending_type` | string | ❌ | "victory", "defeat", "neutral" |
| `children` | object | ✅ | Maps choice text → child node_id |
| `metadata` | object | ❌ | Custom data (location, difficulty, etc.) |

## Example: Complete Story Tree

See `src/orchestrator/story_trees/example-campaign.json` for a full example with:
- Multiple branching paths
- Different ending types
- Metadata for tracking
- Loops back to previous nodes

## Integration with Campaigns

When you start a campaign:

```python
# In orchestrator/app.py
story_tree = StoryTreeLoader.load_story_tree("stormwreck-isle")
```

If a story tree exists:
- ✅ Uses predefined narratives
- ✅ Matches player choices to nodes
- ✅ Guides story toward endings
- ✅ Falls back to AI if no match

If no story tree exists:
- ✅ Runs in free-form mode
- ✅ Uses AI-generated narratives
- ✅ No guaranteed endings

## Player Experience

1. **Choice Buttons**: Players see predefined choices as clickable buttons
2. **Custom Input**: Players can still type their own actions
3. **Fuzzy Matching**: System tries to match custom input to story nodes
4. **AI Fallback**: If no match, uses AI to continue the story
5. **Ending Detection**: When ending is reached, game stops

## Best Practices

1. **Start Simple**: Create a small tree (3-5 nodes) to test
2. **Test All Paths**: Ensure every branch reaches an ending
3. **Clear Choices**: Make choice text clear and distinct
4. **Multiple Endings**: Provide different ending types for replayability
5. **Metadata**: Use metadata to track player progress
6. **Loops**: Allow players to return to previous areas

## Troubleshooting

**Story tree not loading?**
- Check file name matches `{campaign_id}.json`
- Verify JSON is valid (use a JSON validator)
- Check file is in `src/orchestrator/story_trees/`

**Choices not matching?**
- Ensure choice text in `children` matches text in `choices` array
- System does fuzzy matching, but exact matches work best
- Check for typos or extra spaces

**Story not ending?**
- Verify at least one node has `"is_ending": true`
- Check all paths lead to ending nodes
- Test the path manually

## Advanced Features

### Keyword Matching
The system can find nearby nodes based on keywords:
```python
nearby_node = story_tree.find_node_by_keywords(["dragon", "treasure"])
```

### Metadata Tracking
Use metadata to track game state:
```json
"metadata": {
  "location": "Dragon's Lair",
  "items_found": ["sword", "potion"],
  "difficulty": "hard"
}
```

### Dynamic Choices
You can modify choices based on game state (requires code changes in orchestrator).

## Next Steps

1. Create your first story tree JSON file
2. Test it with a campaign
3. Iterate and refine based on player feedback
4. Add more branches and endings for replayability

For more details, see `src/orchestrator/story_trees/README.md`

