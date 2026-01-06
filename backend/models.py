"""
Pydantic Models for Poker Hand Schema

This module defines normalized poker hand data structures with validation.
These models are purely structural - they contain NO poker strategy logic.
"""

from typing import Optional, List, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
import re


class TableType(str, Enum):
    """Valid table types"""
    SIX_MAX = "6max"
    NINE_MAX = "9max"


class Position(str, Enum):
    """Valid poker positions"""
    UTG = "UTG"
    UTG_1 = "UTG+1"
    UTG_2 = "UTG+2"
    MP = "MP"
    MP_1 = "MP+1"
    CO = "CO"
    BTN = "BTN"
    SB = "SB"
    BB = "BB"


class Action(str, Enum):
    """Valid poker actions"""
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    RAISE = "raise"
    BET = "bet"
    ALL_IN = "all_in"


class PreflopDecisionRequest(BaseModel):
    """Request model for preflop decision endpoint."""
    table_type: str = Field(..., description="Table type: 6max or 9max")
    position: str = Field(..., description="Player position")
    hero_hand: str = Field(..., description="Hero's hand (e.g., AKs, 77, QJo)")
    prior_action: str = Field(..., description="Prior action: folded, limpers, or raise")
    
    class Config:
        json_schema_extra = {
            "example": {
                "table_type": "6max",
                "position": "BTN",
                "hero_hand": "AKs",
                "prior_action": "folded"
            }
        }


class LLMAnalysisRequest(BaseModel):
    """Request model for LLM analysis endpoint."""
    hand: str = Field(..., description="Hero's hand (e.g., AKs, 77, QJo)")
    position: str = Field(..., description="Player position")
    table_type: str = Field(..., description="Table type: 6max or 9max")
    action: str = Field(..., description="Action: open, call, or 3bet")
    context: Optional[str] = Field(None, description="Additional context about the situation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "hand": "AKs",
                "position": "BTN",
                "table_type": "6max",
                "action": "open",
                "context": "Against a tight player in the blinds"
            }
        }


class HandAnalysisRequest(BaseModel):
    """Request model for simple hand analysis endpoints."""
    position: str = Field(..., description="Player position")
    hand: str = Field(..., description="Hero's hand (e.g., AKs, 77, QJo)")
    action: str = Field(..., description="Action taken")
    situation: Optional[str] = Field(None, description="Additional situation context")
    mode: Literal["gto", "exploitative", "review"] = Field(
        default="gto",
        description="Analysis mode"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "position": "BTN",
                "hand": "AKs",
                "action": "raise",
                "situation": "First in from button",
                "mode": "gto"
            }
        }


class PokerHandSchema(BaseModel):
    """
    Normalized poker hand schema for storing and analyzing poker hands.
    
    This model is purely structural - it contains NO strategy logic.
    It validates hand data format but makes no poker decisions.
    
    Example usage:
        hand = PokerHandSchema(
            table_type="6max",
            effective_stack_bb=100,
            hero_position="BTN",
            hero_hand="AKs",
            villain_positions=["SB", "BB"],
            preflop_action="BTN raises 2.5bb, SB folds, BB calls",
            flop_board=["Ah", "Kd", "7c"],
            flop_action="BB checks, BTN bets 3bb, BB calls"
        )
    """
    
    # Required fields
    table_type: TableType = Field(
        ...,
        description="Table format: 6max or 9max"
    )
    
    effective_stack_bb: float = Field(
        ...,
        gt=0,
        description="Effective stack size in big blinds (must be positive)"
    )
    
    hero_position: Position = Field(
        ...,
        description="Hero's position at the table"
    )
    
    hero_hand: str = Field(
        ...,
        min_length=2,
        max_length=4,
        description="Hero's hole cards (e.g., AKs, 77, QJo)"
    )
    
    villain_positions: List[Position] = Field(
        ...,
        min_length=1,
        max_length=9,
        description="List of villain positions involved in the hand"
    )
    
    preflop_action: str = Field(
        ...,
        min_length=1,
        description="Description of preflop action sequence"
    )
    
    flop_board: List[str] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Three flop cards (e.g., ['Ah', 'Kd', '7c'])"
    )
    
    flop_action: str = Field(
        ...,
        min_length=1,
        description="Description of flop action sequence"
    )
    
    # Optional fields (turn and river may not be reached)
    turn_card: Optional[str] = Field(
        None,
        description="Turn card (e.g., 'Qh')"
    )
    
    turn_action: Optional[str] = Field(
        None,
        description="Description of turn action sequence"
    )
    
    river_card: Optional[str] = Field(
        None,
        description="River card (e.g., '3s')"
    )
    
    river_action: Optional[str] = Field(
        None,
        description="Description of river action sequence"
    )
    
    villain_notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional notes about villain tendencies or reads"
    )
    
    @field_validator('hero_hand')
    @classmethod
    def validate_hand_notation(cls, v: str) -> str:
        """
        Validate hero hand notation.
        Valid formats: AA, AKs, AKo, 72o, JTs, etc.
        """
        # Pocket pairs: AA, KK, QQ, ..., 22
        pair_pattern = r'^(A|K|Q|J|T|9|8|7|6|5|4|3|2)\1$'
        # Suited/offsuit: AKs, AKo, etc.
        suited_pattern = r'^(A|K|Q|J|T|9|8|7|6|5|4|3|2)(A|K|Q|J|T|9|8|7|6|5|4|3|2)[so]$'
        
        if not (re.match(pair_pattern, v) or re.match(suited_pattern, v)):
            raise ValueError(
                f"Invalid hand notation: {v}. "
                "Use format like: AA, AKs, AKo, 72o, JTs"
            )
        
        # Check for invalid hands (e.g., AA with s/o suffix)
        if len(v) == 3 and v[0] == v[1]:
            raise ValueError(
                f"Invalid hand notation: {v}. "
                "Pocket pairs should not have s/o suffix (e.g., use 'AA' not 'AAs')"
            )
        
        return v
    
    @field_validator('flop_board')
    @classmethod
    def validate_flop_cards(cls, v: List[str]) -> List[str]:
        """Validate flop card notation."""
        if len(v) != 3:
            raise ValueError("Flop must have exactly 3 cards")
        
        for card in v:
            if not cls._is_valid_card(card):
                raise ValueError(
                    f"Invalid card notation: {card}. "
                    "Use format like: Ah, Kd, 7c (rank + suit)"
                )
        
        # Check for duplicate cards
        if len(set(v)) != len(v):
            raise ValueError(f"Duplicate cards in flop: {v}")
        
        return v
    
    @field_validator('turn_card', 'river_card')
    @classmethod
    def validate_single_card(cls, v: Optional[str]) -> Optional[str]:
        """Validate turn/river card notation."""
        if v is None:
            return v
        
        if not cls._is_valid_card(v):
            raise ValueError(
                f"Invalid card notation: {v}. "
                "Use format like: Ah, Kd, 7c (rank + suit)"
            )
        
        return v
    
    @staticmethod
    def _is_valid_card(card: str) -> bool:
        """Check if a card notation is valid."""
        card_pattern = r'^(A|K|Q|J|T|9|8|7|6|5|4|3|2)(h|d|c|s)$'
        return bool(re.match(card_pattern, card))
    
    @model_validator(mode='after')
    def validate_street_consistency(self) -> 'PokerHandSchema':
        """Ensure turn/river actions are provided when cards are present."""
        if self.turn_card and not self.turn_action:
            raise ValueError("turn_action is required when turn_card is provided")
        
        if self.river_card and not self.river_action:
            raise ValueError("river_action is required when river_card is provided")
        
        if self.river_card and not self.turn_card:
            raise ValueError("turn_card is required when river_card is provided")
        
        return self
    
    @model_validator(mode='after')
    def validate_no_duplicate_cards(self) -> 'PokerHandSchema':
        """Ensure no duplicate cards across all streets."""
        all_cards = list(self.flop_board)
        
        if self.turn_card:
            all_cards.append(self.turn_card)
        
        if self.river_card:
            all_cards.append(self.river_card)
        
        if len(set(all_cards)) != len(all_cards):
            raise ValueError(f"Duplicate cards detected across streets: {all_cards}")
        
        return self
    
    @model_validator(mode='after')
    def validate_hero_not_in_villains(self) -> 'PokerHandSchema':
        """Ensure hero position is not in villain positions list."""
        if self.hero_position in self.villain_positions:
            raise ValueError(
                f"Hero position ({self.hero_position}) cannot be in villain_positions list"
            )
        
        return self
    
    def get_board(self) -> List[str]:
        """Get complete board (flop + turn + river)."""
        board = list(self.flop_board)
        if self.turn_card:
            board.append(self.turn_card)
        if self.river_card:
            board.append(self.river_card)
        return board
    
    def get_street(self) -> str:
        """Determine which street the hand reached."""
        if self.river_card:
            return "river"
        elif self.turn_card:
            return "turn"
        else:
            return "flop"
    
    def to_summary(self) -> str:
        """Generate a human-readable hand summary."""
        summary = (
            f"{self.table_type.value} - {self.effective_stack_bb}bb\n"
            f"Hero ({self.hero_position.value}): {self.hero_hand}\n"
            f"Villains: {', '.join(v.value for v in self.villain_positions)}\n"
            f"\nPreflop: {self.preflop_action}\n"
            f"Flop ({' '.join(self.flop_board)}): {self.flop_action}"
        )
        
        if self.turn_card:
            summary += f"\nTurn ({self.turn_card}): {self.turn_action}"
        
        if self.river_card:
            summary += f"\nRiver ({self.river_card}): {self.river_action}"
        
        if self.villain_notes:
            summary += f"\n\nNotes: {self.villain_notes}"
        
        return summary
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "examples": [
                {
                    "table_type": "6max",
                    "effective_stack_bb": 100,
                    "hero_position": "BTN",
                    "hero_hand": "AKs",
                    "villain_positions": ["SB", "BB"],
                    "preflop_action": "Folds to BTN, BTN raises 2.5bb, SB folds, BB calls",
                    "flop_board": ["Ah", "Kd", "7c"],
                    "flop_action": "BB checks, BTN bets 3bb, BB calls",
                    "turn_card": "Qh",
                    "turn_action": "BB checks, BTN bets 8bb, BB folds",
                    "villain_notes": "BB is calling station, rarely folds top pair"
                },
                {
                    "table_type": "9max",
                    "effective_stack_bb": 200,
                    "hero_position": "CO",
                    "hero_hand": "QQ",
                    "villain_positions": ["UTG", "BTN"],
                    "preflop_action": "UTG raises 3bb, folds to CO, CO 3bets 10bb, BTN cold calls, UTG folds",
                    "flop_board": ["Jh", "9s", "2d"],
                    "flop_action": "CO bets 15bb, BTN calls",
                    "turn_card": "Kc",
                    "turn_action": "CO checks, BTN bets 30bb, CO folds"
                },
                {
                    "table_type": "6max",
                    "effective_stack_bb": 50,
                    "hero_position": "SB",
                    "hero_hand": "77",
                    "villain_positions": ["BB"],
                    "preflop_action": "Folds to SB, SB raises 2.5bb, BB calls",
                    "flop_board": ["7h", "6d", "5c"],
                    "flop_action": "SB bets 3bb, BB calls",
                    "turn_card": "4s",
                    "turn_action": "SB bets 8bb, BB raises 20bb, SB all-in 36.5bb, BB calls",
                    "river_card": "Kh",
                    "river_action": "Cards revealed: Hero shows 77 for set, Villain shows 89o for straight",
                    "villain_notes": "Aggressive player, likes to bluff draws"
                }
            ]
        }


class PlayerEquity(BaseModel):
    """Model for a single player in equity calculation."""
    id: str = Field(..., description="Player identifier (e.g., 'Player1', 'Hero', 'Villain')")
    hole_cards: List[str] = Field(
        ...,
        min_length=2,
        max_length=2,
        description="Two hole cards (e.g., ['Ah', 'Kh'])"
    )
    
    @field_validator('hole_cards')
    @classmethod
    def validate_hole_cards(cls, v: List[str]) -> List[str]:
        """Validate hole card notation."""
        if len(v) != 2:
            raise ValueError("Each player must have exactly 2 hole cards")
        
        card_pattern = r'^(A|K|Q|J|T|9|8|7|6|5|4|3|2)(h|d|c|s)$'
        for card in v:
            if not re.match(card_pattern, card):
                raise ValueError(
                    f"Invalid card notation: {card}. "
                    "Use format like: Ah, Kd, 7c, Ts (rank + suit)"
                )
        
        # Check for duplicate hole cards
        if v[0] == v[1]:
            raise ValueError(f"Player cannot have duplicate hole cards: {v}")
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "Hero",
                "hole_cards": ["Ah", "Kh"]
            }
        }


class EquityCalculatorRequest(BaseModel):
    """Request model for equity calculator endpoint."""
    players: List[PlayerEquity] = Field(
        ..., 
        min_length=2,
        max_length=6,
        description="List of players with IDs and hole cards (2-6 players)"
    )
    board_cards: Optional[List[str]] = Field(
        None,
        max_length=5,
        description="Community cards (0-5 cards, e.g., ['As', 'Kd', '7c'])"
    )
    iterations: Optional[int] = Field(
        20000,
        ge=1000,
        le=100000,
        description="Number of Monte Carlo simulations (1,000 - 100,000)"
    )
    
    @field_validator('board_cards')
    @classmethod
    def validate_board_cards(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate board card notation and size."""
        if v is None:
            return v
        
        if len(v) > 5:
            raise ValueError("Board cannot have more than 5 cards")
        
        card_pattern = r'^(A|K|Q|J|T|9|8|7|6|5|4|3|2)(h|d|c|s)$'
        for card in v:
            if not re.match(card_pattern, card):
                raise ValueError(
                    f"Invalid card notation: {card}. "
                    "Use format like: Ah, Kd, 7c, Ts (rank + suit)"
                )
        
        # Check for duplicate board cards
        if len(set(v)) != len(v):
            raise ValueError(f"Duplicate cards in board: {v}")
        
        return v
    
    @model_validator(mode='after')
    def validate_no_duplicate_cards_across_players(self) -> 'EquityCalculatorRequest':
        """Ensure no duplicate cards across all players and board."""
        all_cards = []
        
        # Collect all hole cards
        for player in self.players:
            all_cards.extend(player.hole_cards)
        
        # Collect board cards
        if self.board_cards:
            all_cards.extend(self.board_cards)
        
        # Check for duplicates
        if len(set(all_cards)) != len(all_cards):
            duplicates = [card for card in set(all_cards) if all_cards.count(card) > 1]
            raise ValueError(f"Duplicate cards detected: {', '.join(duplicates)}")
        
        return self
    
    @model_validator(mode='after')
    def validate_unique_player_ids(self) -> 'EquityCalculatorRequest':
        """Ensure all player IDs are unique."""
        player_ids = [player.id for player in self.players]
        if len(set(player_ids)) != len(player_ids):
            duplicates = [pid for pid in set(player_ids) if player_ids.count(pid) > 1]
            raise ValueError(f"Duplicate player IDs: {', '.join(duplicates)}")
        
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "players": [
                    {"id": "Hero", "hole_cards": ["Ah", "Kh"]},
                    {"id": "Villain", "hole_cards": ["Qd", "Qc"]}
                ],
                "board_cards": ["As", "Kd", "7c"],
                "iterations": 20000
            }
        }
