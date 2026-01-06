# Poker Range Data Files

## Important Notice

**All poker ranges are user-defined and can be edited manually.**

This backend contains NO poker strategy assumptions. All strategy decisions are loaded from JSON files in this directory.

## File Format

Each range file must follow this naming convention:
```
{table_type}_{position}_{action}.json
```

Examples:
- `6max_BTN_open.json` - Button opening range for 6-max
- `6max_UTG_open.json` - UTG opening range for 6-max
- `9max_CO_3bet.json` - Cutoff 3-bet range for 9-max

## Required Fields

Each JSON file must contain:

```json
{
  "table_type": "6max" or "9max",
  "position": "UTG" | "MP" | "CO" | "BTN" | "SB" | "BB",
  "action": "open" | "call" | "3bet",
  "hands": {
    "AA": "raise",
    "KK": "raise",
    "72o": "fold",
    ...
  },
  "explanations": {
    "AA": "Premium pocket pair with massive equity.",
    ...
  }
}
```

## Full 13×13 Matrix (169 Hands)

Each range file should define all 169 poker hands:
- **Pairs (13)**: AA, KK, QQ, JJ, TT, 99, 88, 77, 66, 55, 44, 33, 22
- **Suited (78)**: AKs, AQs, ..., 32s
- **Offsuit (78)**: AKo, AQo, ..., 32o

**Missing hands will automatically default to "fold"** with an explanation telling the user to edit the JSON file.

## Valid Actions

- `"raise"` - Open raise or raise
- `"call"` - Call an existing bet
- `"fold"` - Fold the hand
- `"3bet"` - Re-raise (3-bet)

## Sample Data

The file `6max_BTN_open.json` contains **SAMPLE PLACEHOLDER DATA** for demonstration purposes. This is not GTO strategy - it's just example data to show the format.

You should:
1. Copy this file as a template
2. Edit the hands and explanations to match your preferred strategy
3. Create additional files for other positions and situations

## How to Add New Ranges

1. Create a new JSON file following the naming convention
2. Copy the structure from `6max_BTN_open.json`
3. Define the action for each of the 169 hands
4. Add explanations for key hands
5. Restart the backend server to load the new range

## Example: Creating UTG Range

```bash
cp 6max_BTN_open.json 6max_UTG_open.json
# Edit 6max_UTG_open.json
# Change position to "UTG"
# Tighten the range (more folds)
# Update explanations
```

## Validation

The backend will validate:
- File structure (required fields present)
- Hand notation (e.g., "AKs", "77", "QJo")
- Action values (must be "raise", "call", "fold", or "3bet")
- Position/table type combinations

The backend will NOT validate poker strategy - you can define any range you want!

## Backend Behavior

- Missing range files → All hands default to "fold"
- Missing hands in a file → Those hands default to "fold"
- Invalid hand notation → Ignored with a warning
- Invalid action → Error (file won't load)

This ensures the system never crashes due to missing data.
