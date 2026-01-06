"""
Test Suite for Poker Hand Schema Models

Demonstrates validation rules and usage examples.
Run with: python test_models.py
"""

from models import PokerHandSchema, HandAnalysisRequest
from pydantic import ValidationError


def test_valid_complete_hand():
    """Test a valid complete hand (all streets)."""
    hand = PokerHandSchema(
        table_type="6max",
        effective_stack_bb=100,
        hero_position="BTN",
        hero_hand="AKs",
        villain_positions=["SB", "BB"],
        preflop_action="Folds to BTN, BTN raises 2.5bb, SB folds, BB calls",
        flop_board=["Ah", "Kd", "7c"],
        flop_action="BB checks, BTN bets 3bb, BB calls",
        turn_card="Qh",
        turn_action="BB checks, BTN bets 8bb, BB folds"
    )
    
    assert hand.table_type.value == "6max"
    assert hand.get_street() == "turn"
    assert len(hand.get_board()) == 4
    print("✓ Valid complete hand test passed")


def test_valid_flop_only_hand():
    """Test a valid hand that ends on flop."""
    hand = PokerHandSchema(
        table_type="9max",
        effective_stack_bb=200,
        hero_position="CO",
        hero_hand="QQ",
        villain_positions=["UTG"],
        preflop_action="UTG raises 3bb, folds to CO, CO 3bets 10bb, UTG calls",
        flop_board=["Jh", "9s", "2d"],
        flop_action="UTG checks, CO bets 15bb, UTG folds"
    )
    
    assert hand.get_street() == "flop"
    assert len(hand.get_board()) == 3
    print("✓ Valid flop-only hand test passed")


def test_valid_pocket_pairs():
    """Test valid pocket pair notations."""
    valid_pairs = ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22"]
    
    for pair in valid_pairs:
        hand = PokerHandSchema(
            table_type="6max",
            effective_stack_bb=100,
            hero_position="BTN",
            hero_hand=pair,
            villain_positions=["BB"],
            preflop_action="BTN raises, BB calls",
            flop_board=["Ah", "Kd", "7c"],
            flop_action="BB checks, BTN bets, BB folds"
        )
        assert hand.hero_hand == pair
    
    print(f"✓ All {len(valid_pairs)} pocket pairs validated")


def test_valid_suited_hands():
    """Test valid suited hand notations."""
    suited_hands = ["AKs", "AQs", "KQs", "JTs", "98s", "76s", "54s"]
    
    for hand_str in suited_hands:
        hand = PokerHandSchema(
            table_type="6max",
            effective_stack_bb=100,
            hero_position="BTN",
            hero_hand=hand_str,
            villain_positions=["BB"],
            preflop_action="BTN raises, BB calls",
            flop_board=["Ah", "Kd", "7c"],
            flop_action="BB checks, BTN bets, BB folds"
        )
        assert hand.hero_hand == hand_str
    
    print(f"✓ All {len(suited_hands)} suited hands validated")


def test_valid_offsuit_hands():
    """Test valid offsuit hand notations."""
    offsuit_hands = ["AKo", "AQo", "KQo", "JTo", "98o", "72o"]
    
    for hand_str in offsuit_hands:
        hand = PokerHandSchema(
            table_type="6max",
            effective_stack_bb=100,
            hero_position="BTN",
            hero_hand=hand_str,
            villain_positions=["BB"],
            preflop_action="BTN raises, BB calls",
            flop_board=["Ah", "Kd", "7c"],
            flop_action="BB checks, BTN bets, BB folds"
        )
        assert hand.hero_hand == hand_str
    
    print(f"✓ All {len(offsuit_hands)} offsuit hands validated")


def test_invalid_hand_notation():
    """Test that invalid hand notations are rejected."""
    invalid_hands = [
        "AAs",  # Pairs shouldn't have s/o suffix
        "KKo",  # Pairs shouldn't have s/o suffix
        "ABC",  # Invalid format
        "A",    # Too short
        "AK",   # Missing s/o suffix
        "99s",  # Pairs shouldn't have s/o suffix
    ]
    
    for invalid_hand in invalid_hands:
        try:
            hand = PokerHandSchema(
                table_type="6max",
                effective_stack_bb=100,
                hero_position="BTN",
                hero_hand=invalid_hand,
                villain_positions=["BB"],
                preflop_action="BTN raises, BB calls",
                flop_board=["Ah", "Kd", "7c"],
                flop_action="BB checks, BTN bets, BB folds"
            )
            assert False, f"Should have rejected invalid hand: {invalid_hand}"
        except ValidationError as e:
            pass  # Expected
    
    print(f"✓ All {len(invalid_hands)} invalid hands rejected")


def test_invalid_card_notation():
    """Test that invalid card notations are rejected."""
    invalid_boards = [
        ["Ah", "Kd", "7x"],  # Invalid suit
        ["1h", "Kd", "7c"],  # Invalid rank
        ["Ahh", "Kd", "7c"], # Double suit
        ["A", "Kd", "7c"],   # Missing suit
    ]
    
    for invalid_board in invalid_boards:
        try:
            hand = PokerHandSchema(
                table_type="6max",
                effective_stack_bb=100,
                hero_position="BTN",
                hero_hand="AKs",
                villain_positions=["BB"],
                preflop_action="BTN raises, BB calls",
                flop_board=invalid_board,
                flop_action="BB checks, BTN bets, BB folds"
            )
            assert False, f"Should have rejected invalid board: {invalid_board}"
        except ValidationError:
            pass  # Expected
    
    print(f"✓ All {len(invalid_boards)} invalid card notations rejected")


def test_duplicate_cards_in_flop():
    """Test that duplicate cards in flop are rejected."""
    try:
        hand = PokerHandSchema(
            table_type="6max",
            effective_stack_bb=100,
            hero_position="BTN",
            hero_hand="AKs",
            villain_positions=["BB"],
            preflop_action="BTN raises, BB calls",
            flop_board=["Ah", "Ah", "7c"],  # Duplicate Ah
            flop_action="BB checks, BTN bets, BB folds"
        )
        assert False, "Should have rejected duplicate cards"
    except ValidationError:
        pass  # Expected
    
    print("✓ Duplicate cards in flop rejected")


def test_duplicate_cards_across_streets():
    """Test that duplicate cards across streets are rejected."""
    try:
        hand = PokerHandSchema(
            table_type="6max",
            effective_stack_bb=100,
            hero_position="BTN",
            hero_hand="AKs",
            villain_positions=["BB"],
            preflop_action="BTN raises, BB calls",
            flop_board=["Ah", "Kd", "7c"],
            flop_action="BB checks, BTN bets, BB calls",
            turn_card="Ah",  # Duplicate of flop card
            turn_action="BB checks, BTN bets, BB folds"
        )
        assert False, "Should have rejected duplicate card on turn"
    except ValidationError:
        pass  # Expected
    
    print("✓ Duplicate cards across streets rejected")


def test_turn_card_without_action():
    """Test that turn card without action is rejected."""
    try:
        hand = PokerHandSchema(
            table_type="6max",
            effective_stack_bb=100,
            hero_position="BTN",
            hero_hand="AKs",
            villain_positions=["BB"],
            preflop_action="BTN raises, BB calls",
            flop_board=["Ah", "Kd", "7c"],
            flop_action="BB checks, BTN bets, BB calls",
            turn_card="Qh",
            # Missing turn_action
        )
        assert False, "Should have rejected turn card without action"
    except ValidationError:
        pass  # Expected
    
    print("✓ Turn card without action rejected")


def test_river_without_turn():
    """Test that river card without turn is rejected."""
    try:
        hand = PokerHandSchema(
            table_type="6max",
            effective_stack_bb=100,
            hero_position="BTN",
            hero_hand="AKs",
            villain_positions=["BB"],
            preflop_action="BTN raises, BB calls",
            flop_board=["Ah", "Kd", "7c"],
            flop_action="BB checks, BTN bets, BB calls",
            # Missing turn_card and turn_action
            river_card="Qh",
            river_action="BB checks, BTN bets, BB folds"
        )
        assert False, "Should have rejected river without turn"
    except ValidationError:
        pass  # Expected
    
    print("✓ River without turn rejected")


def test_hero_in_villain_positions():
    """Test that hero can't be in villain positions."""
    try:
        hand = PokerHandSchema(
            table_type="6max",
            effective_stack_bb=100,
            hero_position="BTN",
            hero_hand="AKs",
            villain_positions=["BTN", "BB"],  # Hero is BTN
            preflop_action="BTN raises, BB calls",
            flop_board=["Ah", "Kd", "7c"],
            flop_action="BB checks, BTN bets, BB folds"
        )
        assert False, "Should have rejected hero in villain positions"
    except ValidationError:
        pass  # Expected
    
    print("✓ Hero in villain positions rejected")


def test_negative_stack_size():
    """Test that negative stack sizes are rejected."""
    try:
        hand = PokerHandSchema(
            table_type="6max",
            effective_stack_bb=-100,  # Negative stack
            hero_position="BTN",
            hero_hand="AKs",
            villain_positions=["BB"],
            preflop_action="BTN raises, BB calls",
            flop_board=["Ah", "Kd", "7c"],
            flop_action="BB checks, BTN bets, BB folds"
        )
        assert False, "Should have rejected negative stack"
    except ValidationError:
        pass  # Expected
    
    print("✓ Negative stack size rejected")


def test_helper_methods():
    """Test helper methods."""
    hand = PokerHandSchema(
        table_type="6max",
        effective_stack_bb=100,
        hero_position="BTN",
        hero_hand="AKs",
        villain_positions=["SB", "BB"],
        preflop_action="Folds to BTN, BTN raises 2.5bb, SB folds, BB calls",
        flop_board=["Ah", "Kd", "7c"],
        flop_action="BB checks, BTN bets 3bb, BB calls",
        turn_card="Qh",
        turn_action="BB checks, BTN bets 8bb, BB calls",
        river_card="3s",
        river_action="BB checks, BTN checks",
        villain_notes="BB is passive postflop"
    )
    
    # Test get_board()
    board = hand.get_board()
    assert len(board) == 5
    assert board == ["Ah", "Kd", "7c", "Qh", "3s"]
    
    # Test get_street()
    assert hand.get_street() == "river"
    
    # Test to_summary()
    summary = hand.to_summary()
    assert "6max" in summary
    assert "BTN" in summary
    assert "AKs" in summary
    assert "Notes: BB is passive postflop" in summary
    
    print("✓ All helper methods working correctly")


def test_hand_analysis_request():
    """Test the HandAnalysisRequest model."""
    request = HandAnalysisRequest(
        hand_data={
            "table_type": "6max",
            "effective_stack_bb": 100,
            "hero_position": "BTN",
            "hero_hand": "AKs",
            "villain_positions": ["BB"],
            "preflop_action": "Folds to BTN, BTN raises 2.5bb, BB calls",
            "flop_board": ["Ah", "Kd", "7c"],
            "flop_action": "BB checks, BTN bets 3bb, BB calls"
        },
        analysis_type="full",
        include_range_comparison=True
    )
    
    assert request.analysis_type == "full"
    assert request.include_range_comparison == True
    assert request.hand_data.hero_hand == "AKs"
    
    print("✓ HandAnalysisRequest validation passed")


def test_json_serialization():
    """Test JSON serialization and deserialization."""
    hand_dict = {
        "table_type": "6max",
        "effective_stack_bb": 100,
        "hero_position": "BTN",
        "hero_hand": "AKs",
        "villain_positions": ["BB"],
        "preflop_action": "BTN raises, BB calls",
        "flop_board": ["Ah", "Kd", "7c"],
        "flop_action": "BB checks, BTN bets, BB folds"
    }
    
    # Create from dict
    hand = PokerHandSchema(**hand_dict)
    
    # Serialize to dict
    serialized = hand.model_dump()
    
    # Verify key fields
    assert serialized["table_type"] == "6max"
    assert serialized["hero_hand"] == "AKs"
    
    # Create from serialized
    hand2 = PokerHandSchema(**serialized)
    assert hand2.hero_hand == hand.hero_hand
    
    print("✓ JSON serialization/deserialization working")


if __name__ == "__main__":
    """Run all tests when executed directly."""
    print("\n" + "="*60)
    print("Running Poker Hand Schema Validation Tests")
    print("="*60 + "\n")
    
    test_functions = [
        test_valid_complete_hand,
        test_valid_flop_only_hand,
        test_valid_pocket_pairs,
        test_valid_suited_hands,
        test_valid_offsuit_hands,
        test_invalid_hand_notation,
        test_invalid_card_notation,
        test_duplicate_cards_in_flop,
        test_duplicate_cards_across_streets,
        test_turn_card_without_action,
        test_river_without_turn,
        test_hero_in_villain_positions,
        test_negative_stack_size,
        test_helper_methods,
        test_hand_analysis_request,
        test_json_serialization,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} FAILED: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    if failed == 0:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {failed} test(s) failed")
        exit(1)
