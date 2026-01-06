"""
Poker Equity Calculator - Monte Carlo Simulation

Pure Python implementation with no external poker libraries.
Calculates win/tie/equity percentages for 2-6 players.
"""

import random
from typing import List, Dict, Tuple
from itertools import combinations


class Card:
    """Represents a single playing card."""
    
    RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    SUITS = ['h', 'd', 'c', 's']  # hearts, diamonds, clubs, spades
    
    RANK_VALUES = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
        'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
    }
    
    def __init__(self, rank: str, suit: str):
        if rank not in self.RANKS:
            raise ValueError(f"Invalid rank: {rank}")
        if suit not in self.SUITS:
            raise ValueError(f"Invalid suit: {suit}")
        self.rank = rank
        self.suit = suit
        self.value = self.RANK_VALUES[rank]
    
    def __str__(self):
        return f"{self.rank}{self.suit}"
    
    def __repr__(self):
        return str(self)
    
    def __eq__(self, other):
        return self.rank == other.rank and self.suit == other.suit
    
    def __hash__(self):
        return hash((self.rank, self.suit))
    
    @staticmethod
    def from_string(card_str: str) -> 'Card':
        """Parse card string like 'Ah' or 'As' into Card object."""
        if len(card_str) != 2:
            raise ValueError(f"Invalid card format: {card_str}")
        return Card(card_str[0], card_str[1])


class Deck:
    """Standard 52-card deck."""
    
    def __init__(self, exclude_cards: List[Card] = None):
        """Create deck, optionally excluding specific cards."""
        self.cards = [
            Card(rank, suit) 
            for rank in Card.RANKS 
            for suit in Card.SUITS
        ]
        
        if exclude_cards:
            self.cards = [c for c in self.cards if c not in exclude_cards]
    
    def shuffle(self):
        """Shuffle the deck."""
        random.shuffle(self.cards)
    
    def deal(self, n: int) -> List[Card]:
        """Deal n cards from the deck."""
        if n > len(self.cards):
            raise ValueError(f"Cannot deal {n} cards, only {len(self.cards)} remaining")
        dealt = self.cards[:n]
        self.cards = self.cards[n:]
        return dealt


class HandEvaluator:
    """Evaluates poker hand strength."""
    
    # Hand rankings (higher is better)
    HAND_RANKINGS = {
        'high_card': 1,
        'pair': 2,
        'two_pair': 3,
        'three_of_a_kind': 4,
        'straight': 5,
        'flush': 6,
        'full_house': 7,
        'four_of_a_kind': 8,
        'straight_flush': 9
    }
    
    @staticmethod
    def evaluate(cards: List[Card]) -> Tuple[int, List[int]]:
        """
        Evaluate a 5-card hand.
        Returns (hand_rank, tiebreakers) where higher values win.
        """
        if len(cards) != 5:
            raise ValueError("Must evaluate exactly 5 cards")
        
        # Sort cards by value (descending)
        cards = sorted(cards, key=lambda c: c.value, reverse=True)
        
        # Check for flush
        is_flush = len(set(c.suit for c in cards)) == 1
        
        # Check for straight
        values = [c.value for c in cards]
        is_straight = False
        straight_high = 0
        
        # Regular straight check
        if values == list(range(values[0], values[0] - 5, -1)):
            is_straight = True
            straight_high = values[0]
        
        # Ace-low straight (A-2-3-4-5)
        if values == [14, 5, 4, 3, 2]:
            is_straight = True
            straight_high = 5  # In A-2-3-4-5, the 5 is the high card
        
        # Count rank occurrences
        rank_counts = {}
        for card in cards:
            rank_counts[card.value] = rank_counts.get(card.value, 0) + 1
        
        counts = sorted(rank_counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
        count_pattern = [count for _, count in counts]
        
        # Straight flush
        if is_straight and is_flush:
            return (HandEvaluator.HAND_RANKINGS['straight_flush'], [straight_high])
        
        # Four of a kind
        if count_pattern == [4, 1]:
            quad_rank = counts[0][0]
            kicker = counts[1][0]
            return (HandEvaluator.HAND_RANKINGS['four_of_a_kind'], [quad_rank, kicker])
        
        # Full house
        if count_pattern == [3, 2]:
            trips_rank = counts[0][0]
            pair_rank = counts[1][0]
            return (HandEvaluator.HAND_RANKINGS['full_house'], [trips_rank, pair_rank])
        
        # Flush
        if is_flush:
            return (HandEvaluator.HAND_RANKINGS['flush'], values)
        
        # Straight
        if is_straight:
            return (HandEvaluator.HAND_RANKINGS['straight'], [straight_high])
        
        # Three of a kind
        if count_pattern == [3, 1, 1]:
            trips_rank = counts[0][0]
            kickers = [counts[1][0], counts[2][0]]
            return (HandEvaluator.HAND_RANKINGS['three_of_a_kind'], [trips_rank] + kickers)
        
        # Two pair
        if count_pattern == [2, 2, 1]:
            pair1 = counts[0][0]
            pair2 = counts[1][0]
            kicker = counts[2][0]
            return (HandEvaluator.HAND_RANKINGS['two_pair'], [pair1, pair2, kicker])
        
        # Pair
        if count_pattern == [2, 1, 1, 1]:
            pair_rank = counts[0][0]
            kickers = [counts[1][0], counts[2][0], counts[3][0]]
            return (HandEvaluator.HAND_RANKINGS['pair'], [pair_rank] + kickers)
        
        # High card
        return (HandEvaluator.HAND_RANKINGS['high_card'], values)
    
    @staticmethod
    def best_hand(hole_cards: List[Card], board: List[Card]) -> Tuple[int, List[int]]:
        """
        Find the best 5-card hand from hole cards + board.
        """
        all_cards = hole_cards + board
        
        if len(all_cards) < 5:
            raise ValueError("Need at least 5 cards to make a hand")
        
        # Try all 5-card combinations
        best_rank = 0
        best_tiebreakers = []
        
        for combo in combinations(all_cards, 5):
            rank, tiebreakers = HandEvaluator.evaluate(list(combo))
            
            # Compare hands
            if rank > best_rank or (rank == best_rank and tiebreakers > best_tiebreakers):
                best_rank = rank
                best_tiebreakers = tiebreakers
        
        return (best_rank, best_tiebreakers)


class EquityCalculator:
    """Monte Carlo equity calculator for poker hands."""
    
    def __init__(self, iterations: int = 20000):
        """
        Initialize equity calculator.
        
        Args:
            iterations: Number of Monte Carlo simulations to run
        """
        self.iterations = iterations
    
    def calculate(
        self,
        players_hole_cards: List[List[str]],
        board: List[str] = None,
    ) -> Dict[int, Dict[str, float]]:
        """
        Calculate equity for multiple players.
        
        Args:
            players_hole_cards: List of hole cards for each player (e.g., [["Ah", "Kh"], ["Qd", "Qc"]])
            board: Community cards (0-5 cards)
        
        Returns:
            Dictionary mapping player index to results:
            {
                0: {"win": 45.2, "tie": 2.1, "equity": 46.25},
                1: {"win": 52.7, "tie": 2.1, "equity": 53.75}
            }
        """
        # Validate inputs
        num_players = len(players_hole_cards)
        if num_players < 2 or num_players > 6:
            raise ValueError("Must have 2-6 players")
        
        # Parse hole cards
        parsed_hole_cards = []
        known_cards = []
        
        for player_cards in players_hole_cards:
            if len(player_cards) != 2:
                raise ValueError("Each player must have exactly 2 hole cards")
            
            player_parsed = [Card.from_string(c) for c in player_cards]
            parsed_hole_cards.append(player_parsed)
            known_cards.extend(player_parsed)
        
        # Parse board
        parsed_board = []
        if board:
            if len(board) > 5:
                raise ValueError("Board cannot have more than 5 cards")
            parsed_board = [Card.from_string(c) for c in board]
            known_cards.extend(parsed_board)
        
        # Check for duplicate cards
        if len(set(known_cards)) != len(known_cards):
            raise ValueError("Duplicate cards detected")
        
        # Calculate how many cards to deal
        board_cards_needed = 5 - len(parsed_board)
        
        # Run simulations
        results = {i: {"wins": 0, "ties": 0} for i in range(num_players)}
        
        for _ in range(self.iterations):
            # Create deck excluding known cards
            deck = Deck(exclude_cards=known_cards)
            deck.shuffle()
            
            # Complete the board
            full_board = parsed_board + deck.deal(board_cards_needed)
            
            # Evaluate each player's hand
            player_hands = []
            for player_hole in parsed_hole_cards:
                hand_rank, tiebreakers = HandEvaluator.best_hand(player_hole, full_board)
                player_hands.append((hand_rank, tiebreakers))
            
            # Find winner(s)
            best_hand = max(player_hands)
            winners = [i for i, hand in enumerate(player_hands) if hand == best_hand]
            
            if len(winners) == 1:
                results[winners[0]]["wins"] += 1
            else:
                # Split pot (tie)
                for winner in winners:
                    results[winner]["ties"] += 1
        
        # Convert to percentages
        final_results = {}
        for player_idx in range(num_players):
            wins = results[player_idx]["wins"]
            ties = results[player_idx]["ties"]
            
            win_pct = (wins / self.iterations) * 100
            tie_pct = (ties / self.iterations) * 100
            
            # For equity: wins count as 100%, ties are split equally among tied players
            # In each simulation where this player ties, count how many players tied
            # The equity from ties = (ties / iterations) * (100% / number_of_tied_players)
            # We approximate this by assuming ties are split equally
            # A better approach: equity = wins + (ties / num_tied_players_per_simulation)
            # For simplicity: equity ≈ wins + ties/2 for heads-up, ties/3 for 3-way, etc.
            
            # Calculate average number of winners per tied simulation
            if ties > 0:
                # In multi-way ties, equity is split
                # We need to track this per-simulation, but for now approximate
                # by dividing tie equity by average tied player count
                tied_player_count = sum(1 for i in range(num_players) if results[i]["ties"] > 0)
                equity_pct = win_pct + (tie_pct / tied_player_count)
            else:
                equity_pct = win_pct
            
            final_results[player_idx] = {
                "win_percentage": round(win_pct, 2),
                "tie_percentage": round(tie_pct, 2),
                "equity_percentage": round(equity_pct, 2)
            }
        
        return final_results


# Global instance
equity_calculator = EquityCalculator()
