"""
Preflop Range Loader - Data-Driven Poker Range System

IMPORTANT: This backend contains NO poker strategy assumptions.
All poker ranges are user-defined and loaded from JSON files only.

Poker ranges can be edited manually by modifying JSON files in:
    backend/data/ranges/

Each range file must contain a full 13×13 matrix (169 hands).
Missing hands will automatically default to "fold" with an explanation.

File naming convention: {table_type}_{position}_{action}.json
Example: 6max_BTN_open.json
"""

import json
from pathlib import Path
from typing import Dict, Optional

# Valid poker hands (169 total) - this is poker hand notation, NOT strategy
VALID_PAIRS = ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22"]

VALID_SUITED = [
    "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
    "KQs", "KJs", "KTs", "K9s", "K8s", "K7s", "K6s", "K5s", "K4s", "K3s", "K2s",
    "QJs", "QTs", "Q9s", "Q8s", "Q7s", "Q6s", "Q5s", "Q4s", "Q3s", "Q2s",
    "JTs", "J9s", "J8s", "J7s", "J6s", "J5s", "J4s", "J3s", "J2s",
    "T9s", "T8s", "T7s", "T6s", "T5s", "T4s", "T3s", "T2s",
    "98s", "97s", "96s", "95s", "94s", "93s", "92s",
    "87s", "86s", "85s", "84s", "83s", "82s",
    "76s", "75s", "74s", "73s", "72s",
    "65s", "64s", "63s", "62s",
    "54s", "53s", "52s",
    "43s", "42s",
    "32s"
]

VALID_OFFSUIT = [
    "AKo", "AQo", "AJo", "ATo", "A9o", "A8o", "A7o", "A6o", "A5o", "A4o", "A3o", "A2o",
    "KQo", "KJo", "KTo", "K9o", "K8o", "K7o", "K6o", "K5o", "K4o", "K3o", "K2o",
    "QJo", "QTo", "Q9o", "Q8o", "Q7o", "Q6o", "Q5o", "Q4o", "Q3o", "Q2o",
    "JTo", "J9o", "J8o", "J7o", "J6o", "J5o", "J4o", "J3o", "J2o",
    "T9o", "T8o", "T7o", "T6o", "T5o", "T4o", "T3o", "T2o",
    "98o", "97o", "96o", "95o", "94o", "93o", "92o",
    "87o", "86o", "85o", "84o", "83o", "82o",
    "76o", "75o", "74o", "73o", "72o",
    "65o", "64o", "63o", "62o",
    "54o", "53o", "52o",
    "43o", "42o",
    "32o"
]

ALL_HANDS = VALID_PAIRS + VALID_SUITED + VALID_OFFSUIT  # 169 hands total

# Valid action types (not strategy - just valid JSON values)
VALID_ACTIONS = ["raise", "call", "fold", "3bet"]
VALID_TABLE_TYPES = ["6max", "9max"]
VALID_POSITIONS_6MAX = ["UTG", "MP", "CO", "BTN", "SB", "BB"]
VALID_POSITIONS_9MAX = ["UTG", "UTG+1", "MP", "MP+1", "HJ", "CO", "BTN", "SB", "BB"]
VALID_ACTION_TYPES = ["open", "call", "3bet"]


class RangeData:
    """
    Container for a single range configuration.
    
    Ensures all 169 hands are present. Missing hands default to "fold".
    No poker strategy is encoded here - this is pure data storage.
    """
    
    def __init__(self, data: dict):
        self.table_type = data.get("table_type")
        self.position = data.get("position")
        self.action = data.get("action")
        self.hands = data.get("hands", {})
        self.explanations = data.get("explanations", {})
        
        # Ensure all 169 hands are present (missing hands → fold)
        self._ensure_complete_range()

    def _ensure_complete_range(self):
        """
        Fill in missing hands with "fold" action.
        This ensures every range has all 169 hands defined.
        """
        for hand in ALL_HANDS:
            if hand not in self.hands:
                self.hands[hand] = "fold"
                self.explanations[hand] = (
                    f"Hand not defined in {self.position} {self.action} range. "
                    f"Defaulting to fold. Edit the JSON file to add this hand."
                )

    def get_hand_action(self, hand: str) -> str:
        """Get action for a hand. Always returns a valid action (never None)."""
        return self.hands.get(hand, "fold")

    def get_hand_explanation(self, hand: str) -> str:
        """Get explanation for a hand. Always returns text (never None)."""
        default = f"No explanation provided for {hand} in {self.position} {self.action} range."
        return self.explanations.get(hand, default)


class RangeLoader:
    """
    Loads preflop ranges from JSON files ONLY.
    
    NO poker strategy is hardcoded in this class.
    All ranges are user-defined and stored in data/ranges/ as JSON.
    
    Users can add/edit/delete range files manually.
    """
    
    def __init__(self):
        self.ranges: Dict[str, RangeData] = {}
        self.data_dir = Path(__file__).parent / "data" / "ranges"
        
    def load_all_ranges(self) -> None:
        """
        Load all JSON range files from data/ranges/ directory.
        
        If no files exist, the system will return all-fold defaults.
        """
        if not self.data_dir.exists():
            print(f"⚠️  Range directory not found: {self.data_dir}")
            print(f"    Creating directory. Add JSON range files here.")
            self.data_dir.mkdir(parents=True, exist_ok=True)
            return
        
        json_files = list(self.data_dir.glob("*.json"))
        
        if len(json_files) == 0:
            print(f"⚠️  No range files found in {self.data_dir}")
            print(f"    Add JSON files to define poker ranges.")
            return
        
        print(f"🃏 Loading {len(json_files)} range files from {self.data_dir}")
        
        for json_file in json_files:
            try:
                self._load_range_file(json_file)
            except Exception as e:
                print(f"❌ Error loading {json_file.name}: {e}")
    
    def _load_range_file(self, filepath: Path) -> None:
        """Load a single JSON range file and validate structure."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Validate structure (not strategy)
        self._validate_range_data(data, filepath.name)
        
        # Create unique key
        key = f"{data['table_type']}_{data['position']}_{data['action']}"
        self.ranges[key] = RangeData(data)
        
        # Count actions for logging
        action_counts = {}
        for hand_action in self.ranges[key].hands.values():
            action_counts[hand_action] = action_counts.get(hand_action, 0) + 1
        
        print(f"  ✓ Loaded: {key}")
        print(f"    Actions: {', '.join(f'{k}={v}' for k, v in sorted(action_counts.items()))}")
    
    def _validate_range_data(self, data: dict, filename: str) -> None:
        """
        Validate JSON structure (NOT poker strategy).
        
        Checks:
        - Required fields exist
        - Table type/position/action are valid strings
        - Hand notation is valid (e.g., "AKs", "77")
        - Actions are valid strings (e.g., "raise", "fold")
        """
        # Check required fields
        required_fields = ["table_type", "position", "action", "hands"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field '{field}' in {filename}")
        
        # Validate table type
        if data["table_type"] not in VALID_TABLE_TYPES:
            raise ValueError(
                f"Invalid table_type '{data['table_type']}' in {filename}. "
                f"Must be one of: {VALID_TABLE_TYPES}"
            )
        
        # Validate position
        valid_positions = (
            VALID_POSITIONS_6MAX if data["table_type"] == "6max" 
            else VALID_POSITIONS_9MAX
        )
        if data["position"] not in valid_positions:
            raise ValueError(
                f"Invalid position '{data['position']}' for {data['table_type']} in {filename}. "
                f"Must be one of: {valid_positions}"
            )
        
        # Validate action type
        if data["action"] not in VALID_ACTION_TYPES:
            raise ValueError(
                f"Invalid action '{data['action']}' in {filename}. "
                f"Must be one of: {VALID_ACTION_TYPES}"
            )
        
        # Validate hands format (not strategy)
        for hand, action in data["hands"].items():
            if hand not in ALL_HANDS:
                print(f"  ⚠️  Invalid hand notation '{hand}' in {filename} - will be ignored")
            if action not in VALID_ACTIONS:
                raise ValueError(
                    f"Invalid action '{action}' for hand '{hand}' in {filename}. "
                    f"Must be one of: {VALID_ACTIONS}"
                )
        
        # Info message about missing hands (they'll auto-fill with fold)
        missing_hands = set(ALL_HANDS) - set(data["hands"].keys())
        if missing_hands:
            print(f"  ℹ️  {len(missing_hands)}/169 hands missing - will default to 'fold'")
    
    def get_range(self, table_type: str, position: str, action: str) -> Optional[RangeData]:
        """Get a specific range if it exists, otherwise None."""
        key = f"{table_type}_{position}_{action}"
        return self.ranges.get(key)
    
    def get_range_or_default(self, table_type: str, position: str, action: str) -> RangeData:
        """
        Get a range, or return an all-fold default if not found.
        
        This guarantees NEVER returning None/undefined.
        Missing range files = all hands fold.
        """
        range_data = self.get_range(table_type, position, action)
        
        if range_data is None:
            # Return all-fold default (NO strategy assumptions)
            print(f"⚠️  Range not found: {table_type}/{position}/{action} → defaulting all hands to fold")
            default_data = {
                "table_type": table_type,
                "position": position,
                "action": action,
                "hands": {hand: "fold" for hand in ALL_HANDS},
                "explanations": {
                    hand: (
                        f"Range file not found for {table_type} {position} {action}. "
                        f"Create backend/data/ranges/{table_type}_{position}_{action}.json to define this range."
                    )
                    for hand in ALL_HANDS
                }
            }
            range_data = RangeData(default_data)
        
        return range_data
    
    def get_available_ranges(self) -> dict:
        """Get metadata about loaded ranges (for API endpoint)."""
        ranges_list = []
        for key, range_data in self.ranges.items():
            # Count actions
            action_counts = {}
            for hand_action in range_data.hands.values():
                action_counts[hand_action] = action_counts.get(hand_action, 0) + 1
            
            ranges_list.append({
                "table_type": range_data.table_type,
                "position": range_data.position,
                "action": range_data.action,
                "hand_count": 169,  # Always 169 (missing hands auto-filled)
                "action_counts": action_counts
            })
        
        return {
            "table_types": VALID_TABLE_TYPES,
            "positions": {
                "6max": VALID_POSITIONS_6MAX,
                "9max": VALID_POSITIONS_9MAX
            },
            "actions": VALID_ACTION_TYPES,
            "loaded_ranges": ranges_list,
            "total_ranges": len(self.ranges)
        }
    
    def validate_hand(self, hand: str) -> bool:
        """Check if hand notation is valid (e.g., "AKs", "77", "QJo")."""
        return hand in ALL_HANDS


# Global instance used by FastAPI routes
# Initialized on server startup in main.py
range_loader = RangeLoader()
