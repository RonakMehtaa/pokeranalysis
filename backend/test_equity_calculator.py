"""
Unit tests for poker equity calculator and hand evaluator.

Tests cover:
- Hand ranking correctness
- Hand comparison logic
- Tie scenarios
- Multi-way pots
- Edge cases
"""

import pytest
from services.equity_calculator import Card, HandEvaluator, EquityCalculator, Deck


class TestCard:
    """Test Card class functionality."""
    
    def test_card_creation(self):
        """Test creating valid cards."""
        card = Card('A', 'h')
        assert card.rank == 'A'
        assert card.suit == 'h'
        assert card.value == 14
    
    def test_card_from_string(self):
        """Test parsing card strings."""
        card = Card.from_string('Kd')
        assert card.rank == 'K'
        assert card.suit == 'd'
        assert card.value == 13
    
    def test_invalid_rank(self):
        """Test that invalid ranks raise ValueError."""
        with pytest.raises(ValueError):
            Card('X', 'h')
    
    def test_invalid_suit(self):
        """Test that invalid suits raise ValueError."""
        with pytest.raises(ValueError):
            Card('A', 'x')
    
    def test_card_equality(self):
        """Test card equality comparison."""
        card1 = Card('A', 'h')
        card2 = Card('A', 'h')
        card3 = Card('K', 'h')
        
        assert card1 == card2
        assert card1 != card3


class TestHandEvaluator:
    """Test hand evaluation logic."""
    
    def test_royal_flush(self):
        """Test royal flush identification."""
        cards = [
            Card('A', 'h'),
            Card('K', 'h'),
            Card('Q', 'h'),
            Card('J', 'h'),
            Card('T', 'h')
        ]
        rank, tiebreakers = HandEvaluator.evaluate(cards)
        assert rank == HandEvaluator.HAND_RANKINGS['straight_flush']
        assert tiebreakers == [14]  # Ace-high straight
    
    def test_straight_flush(self):
        """Test straight flush identification."""
        cards = [
            Card('9', 'c'),
            Card('8', 'c'),
            Card('7', 'c'),
            Card('6', 'c'),
            Card('5', 'c')
        ]
        rank, tiebreakers = HandEvaluator.evaluate(cards)
        assert rank == HandEvaluator.HAND_RANKINGS['straight_flush']
        assert tiebreakers == [9]
    
    def test_four_of_a_kind(self):
        """Test four of a kind identification."""
        cards = [
            Card('K', 'h'),
            Card('K', 'd'),
            Card('K', 'c'),
            Card('K', 's'),
            Card('3', 'h')
        ]
        rank, tiebreakers = HandEvaluator.evaluate(cards)
        assert rank == HandEvaluator.HAND_RANKINGS['four_of_a_kind']
        assert tiebreakers[0] == 13  # King
        assert tiebreakers[1] == 3   # 3 kicker
    
    def test_full_house(self):
        """Test full house identification."""
        cards = [
            Card('Q', 'h'),
            Card('Q', 'd'),
            Card('Q', 'c'),
            Card('7', 's'),
            Card('7', 'h')
        ]
        rank, tiebreakers = HandEvaluator.evaluate(cards)
        assert rank == HandEvaluator.HAND_RANKINGS['full_house']
        assert tiebreakers == [12, 7]  # Queens over 7s
    
    def test_flush(self):
        """Test flush identification."""
        cards = [
            Card('A', 'd'),
            Card('J', 'd'),
            Card('9', 'd'),
            Card('6', 'd'),
            Card('3', 'd')
        ]
        rank, tiebreakers = HandEvaluator.evaluate(cards)
        assert rank == HandEvaluator.HAND_RANKINGS['flush']
        assert tiebreakers == [14, 11, 9, 6, 3]
    
    def test_straight(self):
        """Test straight identification."""
        cards = [
            Card('J', 'h'),
            Card('T', 'd'),
            Card('9', 'c'),
            Card('8', 's'),
            Card('7', 'h')
        ]
        rank, tiebreakers = HandEvaluator.evaluate(cards)
        assert rank == HandEvaluator.HAND_RANKINGS['straight']
        assert tiebreakers == [11]  # Jack-high straight
    
    def test_ace_low_straight(self):
        """Test ace-low straight (wheel)."""
        cards = [
            Card('A', 'h'),
            Card('5', 'd'),
            Card('4', 'c'),
            Card('3', 's'),
            Card('2', 'h')
        ]
        rank, tiebreakers = HandEvaluator.evaluate(cards)
        assert rank == HandEvaluator.HAND_RANKINGS['straight']
        assert tiebreakers == [5]  # 5-high straight (wheel)
    
    def test_three_of_a_kind(self):
        """Test three of a kind identification."""
        cards = [
            Card('8', 'h'),
            Card('8', 'd'),
            Card('8', 'c'),
            Card('A', 's'),
            Card('K', 'h')
        ]
        rank, tiebreakers = HandEvaluator.evaluate(cards)
        assert rank == HandEvaluator.HAND_RANKINGS['three_of_a_kind']
        assert tiebreakers[0] == 8
        assert set(tiebreakers[1:]) == {14, 13}  # A, K kickers
    
    def test_two_pair(self):
        """Test two pair identification."""
        cards = [
            Card('J', 'h'),
            Card('J', 'd'),
            Card('5', 'c'),
            Card('5', 's'),
            Card('2', 'h')
        ]
        rank, tiebreakers = HandEvaluator.evaluate(cards)
        assert rank == HandEvaluator.HAND_RANKINGS['two_pair']
        assert tiebreakers[0] == 11  # Jacks
        assert tiebreakers[1] == 5   # 5s
        assert tiebreakers[2] == 2   # 2 kicker
    
    def test_one_pair(self):
        """Test one pair identification."""
        cards = [
            Card('T', 'h'),
            Card('T', 'd'),
            Card('A', 'c'),
            Card('7', 's'),
            Card('3', 'h')
        ]
        rank, tiebreakers = HandEvaluator.evaluate(cards)
        assert rank == HandEvaluator.HAND_RANKINGS['pair']
        assert tiebreakers[0] == 10
        assert set(tiebreakers[1:]) == {14, 7, 3}
    
    def test_high_card(self):
        """Test high card identification."""
        cards = [
            Card('A', 'h'),
            Card('K', 'd'),
            Card('Q', 'c'),
            Card('7', 's'),
            Card('2', 'h')
        ]
        rank, tiebreakers = HandEvaluator.evaluate(cards)
        assert rank == HandEvaluator.HAND_RANKINGS['high_card']
        assert tiebreakers == [14, 13, 12, 7, 2]


class TestHandComparison:
    """Test hand comparison logic."""
    
    def test_flush_beats_straight(self):
        """Test that flush beats straight."""
        flush = [Card('A', 'd'), Card('J', 'd'), Card('9', 'd'), Card('6', 'd'), Card('3', 'd')]
        straight = [Card('J', 'h'), Card('T', 'd'), Card('9', 'c'), Card('8', 's'), Card('7', 'h')]
        
        flush_rank, flush_tb = HandEvaluator.evaluate(flush)
        straight_rank, straight_tb = HandEvaluator.evaluate(straight)
        
        assert flush_rank > straight_rank
    
    def test_full_house_beats_flush(self):
        """Test that full house beats flush."""
        full_house = [Card('Q', 'h'), Card('Q', 'd'), Card('Q', 'c'), Card('7', 's'), Card('7', 'h')]
        flush = [Card('A', 'd'), Card('J', 'd'), Card('9', 'd'), Card('6', 'd'), Card('3', 'd')]
        
        fh_rank, fh_tb = HandEvaluator.evaluate(full_house)
        flush_rank, flush_tb = HandEvaluator.evaluate(flush)
        
        assert fh_rank > flush_rank
    
    def test_higher_pair_wins(self):
        """Test that higher pair beats lower pair."""
        high_pair = [Card('K', 'h'), Card('K', 'd'), Card('5', 'c'), Card('3', 's'), Card('2', 'h')]
        low_pair = [Card('Q', 'h'), Card('Q', 'd'), Card('A', 'c'), Card('J', 's'), Card('9', 'h')]
        
        high_rank, high_tb = HandEvaluator.evaluate(high_pair)
        low_rank, low_tb = HandEvaluator.evaluate(low_pair)
        
        assert high_rank == low_rank  # Both are pairs
        assert high_tb > low_tb  # Kings beat Queens
    
    def test_kicker_comparison(self):
        """Test kicker comparison for same pair."""
        pair_ace_kicker = [Card('T', 'h'), Card('T', 'd'), Card('A', 'c'), Card('5', 's'), Card('2', 'h')]
        pair_king_kicker = [Card('T', 'c'), Card('T', 's'), Card('K', 'h'), Card('5', 'd'), Card('2', 'c')]
        
        ace_rank, ace_tb = HandEvaluator.evaluate(pair_ace_kicker)
        king_rank, king_tb = HandEvaluator.evaluate(pair_king_kicker)
        
        assert ace_rank == king_rank  # Both have tens
        assert ace_tb > king_tb  # Ace kicker beats King kicker


class TestBestHand:
    """Test best 5-card hand selection from 7 cards."""
    
    def test_best_hand_selection(self):
        """Test selecting best hand from hole cards + board."""
        hole_cards = [Card('A', 'h'), Card('K', 'h')]
        board = [Card('Q', 'h'), Card('J', 'h'), Card('T', 'h')]
        
        rank, tiebreakers = HandEvaluator.best_hand(hole_cards, board)
        
        # Should find royal flush
        assert rank == HandEvaluator.HAND_RANKINGS['straight_flush']
        assert tiebreakers == [14]
    
    def test_best_hand_with_full_board(self):
        """Test best hand with full 5-card board."""
        hole_cards = [Card('A', 's'), Card('A', 'h')]
        board = [
            Card('A', 'd'),
            Card('K', 'c'),
            Card('K', 's'),
            Card('7', 'h'),
            Card('2', 'd')
        ]
        
        rank, tiebreakers = HandEvaluator.best_hand(hole_cards, board)
        
        # Should find full house (AAA over KK)
        assert rank == HandEvaluator.HAND_RANKINGS['full_house']
        assert tiebreakers == [14, 13]


class TestTieScenarios:
    """Test tie scenarios between players."""
    
    def test_identical_hands_tie(self):
        """Test that identical hands result in tie."""
        hand1 = [Card('A', 'h'), Card('K', 'd'), Card('Q', 'c'), Card('J', 's'), Card('T', 'h')]
        hand2 = [Card('A', 'd'), Card('K', 'c'), Card('Q', 's'), Card('J', 'h'), Card('T', 'd')]
        
        rank1, tb1 = HandEvaluator.evaluate(hand1)
        rank2, tb2 = HandEvaluator.evaluate(hand2)
        
        assert rank1 == rank2
        assert tb1 == tb2
    
    def test_board_plays_tie(self):
        """Test when board is the best hand for all players."""
        # Board: Royal flush in hearts
        board = [Card('A', 'h'), Card('K', 'h'), Card('Q', 'h'), Card('J', 'h'), Card('T', 'h')]
        
        # Player 1 hole cards (don't help)
        hole1 = [Card('2', 'd'), Card('3', 'c')]
        # Player 2 hole cards (don't help)
        hole2 = [Card('7', 's'), Card('8', 'd')]
        
        rank1, tb1 = HandEvaluator.best_hand(hole1, board)
        rank2, tb2 = HandEvaluator.best_hand(hole2, board)
        
        assert rank1 == rank2
        assert tb1 == tb2


class TestEquityCalculator:
    """Test equity calculator Monte Carlo simulation."""
    
    def test_aces_vs_kings_preflop(self):
        """Test AA vs KK preflop (AA should win ~80%)."""
        calc = EquityCalculator(iterations=5000)
        
        results = calc.calculate(
            players_hole_cards=[["Ah", "As"], ["Kd", "Kc"]],
            board=None
        )
        
        # AA should have significant edge
        assert results[0]["equity_percentage"] > 70
        assert results[0]["equity_percentage"] < 90
        assert results[1]["equity_percentage"] < 30
    
    def test_dominated_hand(self):
        """Test AK vs AQ preflop (AK dominates)."""
        calc = EquityCalculator(iterations=5000)
        
        results = calc.calculate(
            players_hole_cards=[["Ah", "Kh"], ["Ad", "Qd"]],
            board=None
        )
        
        # AK should dominate AQ
        assert results[0]["equity_percentage"] > 65
        assert results[1]["equity_percentage"] < 35
    
    def test_made_hand_vs_draw(self):
        """Test made pair vs flush draw on flop."""
        calc = EquityCalculator(iterations=5000)
        
        # Board: Ah Kd 7c
        # Player 1: As Kc (top two pair)
        # Player 2: Qd Jd (flush draw)
        results = calc.calculate(
            players_hole_cards=[["As", "Kc"], ["Qd", "Jd"]],
            board=["Ah", "Kd", "7c"]
        )
        
        # Top two pair should be favorite against flush draw
        assert results[0]["equity_percentage"] > 55
    
    def test_three_way_pot(self):
        """Test three-way equity calculation."""
        calc = EquityCalculator(iterations=5000)
        
        results = calc.calculate(
            players_hole_cards=[
                ["Ah", "As"],  # Aces
                ["Kd", "Kc"],  # Kings
                ["Qh", "Qs"]   # Queens
            ],
            board=None
        )
        
        # Aces should be favorite
        assert results[0]["equity_percentage"] > results[1]["equity_percentage"]
        assert results[1]["equity_percentage"] > results[2]["equity_percentage"]
        
        # Equities should sum to approximately 100%
        total_equity = sum(r["equity_percentage"] for r in results.values())
        assert 99 < total_equity < 101
    
    def test_completed_board(self):
        """Test equity with completed board (no randomness)."""
        calc = EquityCalculator(iterations=100)  # Few iterations needed
        
        # Board makes Broadway straight for player 1
        results = calc.calculate(
            players_hole_cards=[
                ["Ah", "Kh"],  # Has Broadway
                ["Qd", "Qc"]   # Has set of queens
            ],
            board=["Qs", "Jd", "Th", "9c", "8s"]
        )
        
        # Player 1 should win 100% with Broadway straight
        assert results[0]["win_percentage"] == 100.0
        assert results[1]["win_percentage"] == 0.0
    
    def test_tie_scenario(self):
        """Test pot splitting with tied hands."""
        calc = EquityCalculator(iterations=1000)
        
        # Board: A K Q J T (Broadway)
        # Both players have Broadway
        results = calc.calculate(
            players_hole_cards=[
                ["2h", "3d"],  # Board plays
                ["4c", "5s"]   # Board plays
            ],
            board=["As", "Kh", "Qd", "Jc", "Ts"]
        )
        
        # Should tie every time
        assert results[0]["tie_percentage"] == 100.0
        assert results[1]["tie_percentage"] == 100.0
        assert results[0]["equity_percentage"] == 50.0
        assert results[1]["equity_percentage"] == 50.0
    
    def test_invalid_player_count(self):
        """Test that invalid player counts raise errors."""
        calc = EquityCalculator()
        
        # Too few players
        with pytest.raises(ValueError):
            calc.calculate(players_hole_cards=[["Ah", "As"]])
        
        # Too many players
        with pytest.raises(ValueError):
            calc.calculate(
                players_hole_cards=[
                    ["Ah", "As"], ["Kh", "Ks"], ["Qh", "Qs"],
                    ["Jh", "Js"], ["Th", "Ts"], ["9h", "9s"],
                    ["8h", "8s"]  # 7th player
                ]
            )
    
    def test_duplicate_cards_error(self):
        """Test that duplicate cards raise error."""
        calc = EquityCalculator()
        
        with pytest.raises(ValueError):
            calc.calculate(
                players_hole_cards=[["Ah", "As"], ["Ah", "Kd"]],  # Ah duplicated
                board=None
            )
    
    def test_invalid_board_size(self):
        """Test that invalid board sizes raise error."""
        calc = EquityCalculator()
        
        with pytest.raises(ValueError):
            calc.calculate(
                players_hole_cards=[["Ah", "As"], ["Kd", "Kc"]],
                board=["2h", "3d", "4c", "5s", "6h", "7d"]  # 6 cards
            )


class TestMultiwayPots:
    """Test multiway pot scenarios."""
    
    def test_four_way_all_in(self):
        """Test four-way all-in scenario."""
        calc = EquityCalculator(iterations=5000)
        
        results = calc.calculate(
            players_hole_cards=[
                ["Ah", "As"],  # Aces
                ["Kd", "Kc"],  # Kings
                ["Ac", "Kh"],  # AK
                ["Qh", "Qs"]   # Queens
            ],
            board=None
        )
        
        # Aces should be favorite
        assert results[0]["equity_percentage"] > 30
        
        # All equities should sum to 100
        total = sum(r["equity_percentage"] for r in results.values())
        assert 99 < total < 101
    
    def test_multiway_with_flop(self):
        """Test three-way pot after flop."""
        calc = EquityCalculator(iterations=5000)
        
        # Flop: Ah Kh 7d
        results = calc.calculate(
            players_hole_cards=[
                ["As", "Kc"],  # Top two pair
                ["Qh", "Jh"],  # Royal flush draw
                ["7h", "7s"]   # Set of 7s
            ],
            board=["Ah", "Kh", "7d"]
        )
        
        # Set should be favorite on this board
        assert results[2]["equity_percentage"] > 40
        
        # Verify all equities sum to 100
        total = sum(r["equity_percentage"] for r in results.values())
        assert 99 < total < 101


class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_wheel_straight(self):
        """Test ace-low straight (A-2-3-4-5)."""
        cards = [Card('A', 'h'), Card('5', 'd'), Card('4', 'c'), Card('3', 's'), Card('2', 'h')]
        rank, tiebreakers = HandEvaluator.evaluate(cards)
        
        assert rank == HandEvaluator.HAND_RANKINGS['straight']
        assert tiebreakers == [5]  # 5-high, not Ace-high
    
    def test_wheel_straight_flush(self):
        """Test ace-low straight flush (steel wheel)."""
        cards = [Card('A', 'h'), Card('5', 'h'), Card('4', 'h'), Card('3', 'h'), Card('2', 'h')]
        rank, tiebreakers = HandEvaluator.evaluate(cards)
        
        assert rank == HandEvaluator.HAND_RANKINGS['straight_flush']
        assert tiebreakers == [5]
    
    def test_all_same_suit_not_flush(self):
        """Test that not all same-suit combinations are flushes."""
        # Only 4 of the same suit
        cards = [Card('A', 'h'), Card('K', 'h'), Card('Q', 'h'), Card('J', 'h'), Card('T', 's')]
        rank, tiebreakers = HandEvaluator.evaluate(cards)
        
        # Should be straight, not flush
        assert rank == HandEvaluator.HAND_RANKINGS['straight']
    
    def test_minimum_iterations(self):
        """Test equity calculator with minimum iterations."""
        calc = EquityCalculator(iterations=1000)
        
        results = calc.calculate(
            players_hole_cards=[["Ah", "As"], ["Kd", "Kc"]],
            board=None
        )
        
        # Should still provide reasonable results
        assert 0 < results[0]["equity_percentage"] < 100
        assert 0 < results[1]["equity_percentage"] < 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
