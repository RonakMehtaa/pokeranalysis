"""
API Routes for Poker Analysis App

IMPORTANT: These routes contain NO poker strategy logic.
All poker decisions are loaded from user-defined JSON range files.

Poker ranges are user-defined and can be edited manually in:
    backend/data/ranges/

This API is purely a data delivery layer with no hardcoded strategy.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from range_loader import range_loader
from services.llm_client import ollama_client
from services.equity_calculator import equity_calculator, EquityCalculator
from models import PokerHandSchema, HandAnalysisRequest, PreflopDecisionRequest, LLMAnalysisRequest, EquityCalculatorRequest, ChatMessageRequest
from typing import Literal
from pathlib import Path

router = APIRouter()

# Path to prompt templates
PROMPTS_DIR = Path(__file__).parent / "prompts"

def load_prompt_template(template_name: str) -> str:
    """
    Load a prompt template from the prompts directory.
    
    Args:
        template_name: Name of the template file (without .txt extension)
    
    Returns:
        Template content as string
    
    Raises:
        HTTPException if template file not found
    """
    template_path = PROMPTS_DIR / f"{template_name}.txt"
    try:
        return template_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail=f"Prompt template not found: {template_name}.txt"
        )

@router.get("/ranges")
def get_available_ranges():
    """
    Get metadata about loaded ranges.
    
    Returns information about which range files are currently loaded.
    No poker strategy is returned - just file metadata.
    """
    return range_loader.get_available_ranges()

@router.get("/range")
def get_range(
    table_type: str = Query(..., description="Table type: 6max or 9max"),
    position: str = Query(..., description="Position: UTG, MP, CO, BTN, SB, BB"),
    action: str = Query(..., description="Action: open, call, or 3bet")
):
    """
    Get full 13×13 hand matrix (169 hands) for a specific range.
    
    Returns user-defined range from JSON file.
    If file doesn't exist, returns all-fold default.
    
    Poker ranges are user-defined and can be edited manually.
    """
    # Get range from JSON file (or all-fold default if missing)
    range_data = range_loader.get_range_or_default(table_type, position, action)
    
    return {
        "table_type": range_data.table_type,
        "position": range_data.position,
        "action": range_data.action,
        "hands": range_data.hands,  # All 169 hands (missing → fold)
        "explanations": range_data.explanations
    }

@router.post("/decision/preflop")
def get_preflop_decision(request: PreflopDecisionRequest):
    """
    Get recommended action for a specific hand from user-defined ranges.
    
    This endpoint contains NO poker strategy logic.
    All decisions come from JSON files in backend/data/ranges/
    
    Parameters:
    - table_type: 6max or 9max
    - position: Player position
    - hero_hand: Hand notation (e.g., AKs, 77, QJo)
    - prior_action: folded, limpers, or raise
    
    Returns action from JSON file (or "fold" if file doesn't exist).
    """
    # Validate hand notation format
    if not range_loader.validate_hand(request.hero_hand):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid hand format: {request.hero_hand}. Use format like AKs, 77, QJo"
        )
    
    # Currently only "open" action is supported
    if request.prior_action != "folded":
        return {
            "recommended_action": "Coming soon",
            "explanation": (
                "Currently only 'folded to you' scenarios are supported. "
                "To add call/3-bet ranges, create JSON files like: "
                f"backend/data/ranges/{request.table_type}_{request.position}_call.json"
            ),
            "hand": request.hero_hand,
            "table_type": request.table_type,
            "position": request.position,
            "prior_action": request.prior_action
        }
    
    # Load user-defined range from JSON (guaranteed to return something)
    range_data = range_loader.get_range_or_default(request.table_type, request.position, "open")
    
    # Get action for this specific hand (guaranteed to return valid action)
    recommended_action = range_data.get_hand_action(request.hero_hand)
    explanation = range_data.get_hand_explanation(request.hero_hand)
    
    return {
        "recommended_action": recommended_action,
        "explanation": explanation,
        "hand": request.hero_hand,
        "table_type": request.table_type,
        "position": request.position,
        "prior_action": request.prior_action
    }

@router.get("/llm/health")
async def llm_health_check():
    """
    Check Ollama service health and configuration.
    
    Returns information about Ollama connectivity and available models.
    """
    health = await ollama_client.check_health()
    return health

@router.post("/llm/analyze")
async def analyze_hand_with_llm(request: LLMAnalysisRequest):
    """
    Analyze a poker hand using Ollama LLM.
    
    IMPORTANT: This endpoint does NOT generate poker strategy.
    It sends a structured prompt to the LLM and returns the response.
    
    The prompt includes:
    - User-defined range data from JSON files
    - Hand context provided by the user
    - Structured format for analysis
    
    Parameters:
    - hand: Hand notation (e.g., AKs, 77, QJo)
    - position: Player position
    - table_type: 6max or 9max
    - action: open, call, or 3bet
    - context: Additional context about the situation (optional)
    
    Returns:
    - LLM's analysis based on the structured prompt
    """
    # Validate hand format
    if not range_loader.validate_hand(request.hand):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid hand format: {request.hand}. Use format like AKs, 77, QJo"
        )
    
    # Get user-defined range data from JSON
    range_data = range_loader.get_range_or_default(
        request.table_type, 
        request.position, 
        request.action
    )
    
    # Get the recommended action from user-defined range
    recommended_action = range_data.get_hand_action(request.hand)
    explanation = range_data.get_hand_explanation(request.hand)
    
    # Construct prompt (NO poker strategy - just structured data)
    prompt = f"""You are a poker analysis assistant. Analyze the following hand based on the provided range data.

Hand: {request.hand}
Position: {request.position}
Table Type: {request.table_type}
Action Context: {request.action}

Range Data (User-Defined):
- Recommended Action: {recommended_action}
- Range Explanation: {explanation}

Additional Context: {request.context if request.context else "None provided"}

Please provide:
1. A clear explanation of why this hand is played this way in this position
2. Key factors that make this hand {recommended_action}
3. Common mistakes players make with this hand
4. How this hand performs postflop

Keep the analysis educational and focused on learning."""

    try:
        # Send prompt to Ollama (NO strategy generation - just forwarding)
        llm_response = await ollama_client.analyze_hand(prompt)
        
        return {
            "hand": request.hand,
            "position": request.position,
            "table_type": request.table_type,
            "action": request.action,
            "recommended_action": recommended_action,
            "range_explanation": explanation,
            "llm_analysis": llm_response,
            "source": "user_defined_range + llm_analysis"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"LLM service error: {str(e)}"
        )

@router.post("/equity/calculate")
def calculate_equity(request: EquityCalculatorRequest):
    """
    Calculate poker hand equity using Monte Carlo simulation.
    
    This is a pure computational tool - NO poker strategy involved.
    Uses Monte Carlo simulation to calculate win/tie/equity percentages.
    
    Parameters:
    - players: List of players with unique IDs and hole cards (2-6 players)
      - id: Player identifier (e.g., "Hero", "Villain", "Player1")
      - hole_cards: Two cards in format like ["Ah", "Kh"]
    - board_cards: Optional community cards (0-5 cards)
    - iterations: Number of simulations (default: 20,000, range: 1,000-100,000)
    
    Returns:
    - Results for each player with win%, tie%, and equity%
    - Keyed by player ID instead of numeric index
    
    Validation:
    - No duplicate cards across all players and board
    - Valid card notation (As, Kh, Td, 2c, etc.)
    - Board size <= 5
    - Unique player IDs
    - 2-6 players only
    
    Example Request:
        POST /api/equity/calculate
        {
            "players": [
                {"id": "Hero", "hole_cards": ["Ah", "Kh"]},
                {"id": "Villain", "hole_cards": ["Qd", "Qc"]}
            ],
            "board_cards": ["As", "Kd", "7c"],
            "iterations": 20000
        }
        
    Example Response:
        {
            "players": {
                "Hero": {"win_percentage": 87.3, "tie_percentage": 0.5, "equity_percentage": 87.55},
                "Villain": {"win_percentage": 12.2, "tie_percentage": 0.5, "equity_percentage": 12.45}
            },
            "iterations": 20000,
            "board_cards": ["As", "Kd", "7c"],
            "num_players": 2
        }
    """
    try:
        # Create calculator with specified iterations (use default if None)
        calc = EquityCalculator(iterations=request.iterations or 20000)
        
        # Convert players to the format expected by equity calculator
        players_hole_cards = [player.hole_cards for player in request.players]
        
        # Calculate equity (board parameter accepts None or List[str])
        board_param = request.board_cards if request.board_cards else None
        results = calc.calculate(
            players_hole_cards=players_hole_cards,
            board=board_param  # type: ignore
        )
        
        # Map results from numeric indices to player IDs
        player_results = {}
        for idx, player in enumerate(request.players):
            player_results[player.id] = results[idx]
        
        return {
            "players": player_results,
            "iterations": request.iterations or 20000,
            "board_cards": request.board_cards if request.board_cards else [],
            "num_players": len(request.players),
            "note": "Results are approximate based on Monte Carlo simulation"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Equity calculation error: {str(e)}"
        )


@router.post("/analyze")
async def analyze_hand(request: HandAnalysisRequest):
    """
    Analyze a poker hand using LLM.
    
    Args:
        request: Contains hand details and analysis mode
    
    Returns:
        LLM analysis of the hand
    
    Note: This endpoint uses prompt templates from backend/prompts/ directory.
    Templates can be customized by editing the .txt files.
    """
    
    # Load appropriate prompt template based on mode
    if request.mode == "gto":
        template = load_prompt_template("gto")
    elif request.mode == "exploitative":
        template = load_prompt_template("exploitative")
    else:  # review mode
        template = load_prompt_template("review")
    
    # Format the prompt with actual hand details
    prompt = template.format(
        position=request.position,
        hand=request.hand,
        action=request.action,
        situation=request.situation or "No additional context provided"
    )
    
    try:
        response = await ollama_client.analyze_hand(prompt)
        return {"analysis": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")

@router.post("/analyze/postflop")
async def analyze_postflop_hand(
    hand_data: PokerHandSchema,
    analysis_type: Literal["gto", "exploitative", "exploitative_with_notes", "review"]
):
    """
    Analyze a postflop poker hand using LLM.
    
    IMPORTANT: This endpoint does NOT contain poker strategy logic.
    It constructs a prompt from hand data and sends it to Ollama.
    The LLM does all reasoning and strategy analysis.
    
    Analysis Types:
    - "gto": Game theory optimal analysis focusing on balanced play
    - "exploitative": Analysis for exploiting opponent tendencies
    - "exploitative_with_notes": Exploitative analysis using villain_notes field
    - "review": Comprehensive hand review with multiple perspectives
    
    Parameters:
    - hand_data: Complete hand data using PokerHandSchema
    - analysis_type: Type of analysis to perform
    
    Returns:
    - Structured text response from LLM with analysis
    """
    
    # Select appropriate prompt template based on analysis type
    if analysis_type == "gto":
        prompt = _construct_gto_prompt(hand_data)
    elif analysis_type == "exploitative":
        prompt = _construct_exploitative_prompt(hand_data)
    elif analysis_type == "exploitative_with_notes":
        if not hand_data.villain_notes:
            raise HTTPException(
                status_code=400,
                detail="villain_notes field is required for exploitative_with_notes analysis"
            )
        prompt = _construct_exploitative_with_notes_prompt(hand_data)
    elif analysis_type == "review":
        prompt = _construct_review_prompt(hand_data)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid analysis_type: {analysis_type}"
        )
    
    try:
        # Send prompt to Ollama (LLM does all reasoning)
        llm_response = await ollama_client.analyze_hand(prompt)
        
        return {
            "hand_summary": hand_data.to_summary(),
            "analysis_type": analysis_type,
            "street": hand_data.get_street(),
            "board": hand_data.get_board(),
            "analysis": llm_response,
            "disclaimer": "This analysis is generated by an LLM and should be used for learning purposes only."
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"LLM service error: {str(e)}"
        )


def _construct_gto_prompt(hand_data: PokerHandSchema) -> str:
    """
    Construct GTO-focused analysis prompt using template file.
    """
    # Load the GTO template
    template = load_prompt_template("gto")
    
    # Build turn section if turn card exists
    turn_section = ""
    if hand_data.turn_card:
        turn_section = f"\n\nTURN ({hand_data.turn_card}):\n{hand_data.turn_action}"
    
    # Build river section if river card exists
    river_section = ""
    if hand_data.river_card:
        river_section = f"\n\nRIVER ({hand_data.river_card}):\n{hand_data.river_action}"
    
    # Get current street
    street = hand_data.get_street()
    
    # Replace template variables
    prompt = template.replace("{{street}}", street)
    prompt = prompt.replace("{{table_type}}", hand_data.table_type.value)
    prompt = prompt.replace("{{effective_stack_bb}}", str(hand_data.effective_stack_bb))
    prompt = prompt.replace("{{hero_position}}", hand_data.hero_position.value)
    prompt = prompt.replace("{{hero_hand}}", hand_data.hero_hand)
    prompt = prompt.replace("{{villain_positions}}", ', '.join(v.value for v in hand_data.villain_positions))
    prompt = prompt.replace("{{preflop_action}}", hand_data.preflop_action)
    prompt = prompt.replace("{{flop_board}}", ' '.join(hand_data.flop_board))
    prompt = prompt.replace("{{flop_action}}", hand_data.flop_action)
    prompt = prompt.replace("{{turn_section}}", turn_section)
    prompt = prompt.replace("{{river_section}}", river_section)
    
    return prompt


def _construct_exploitative_prompt(hand_data: PokerHandSchema) -> str:
    """
    Construct exploitative analysis prompt using template file.
    """
    # Load the exploitative template
    template = load_prompt_template("exploitative")
    
    # Build turn section if turn card exists
    turn_section = ""
    if hand_data.turn_card:
        turn_section = f"\n\nTURN ({hand_data.turn_card}):\n{hand_data.turn_action}"
    
    # Build river section if river card exists
    river_section = ""
    if hand_data.river_card:
        river_section = f"\n\nRIVER ({hand_data.river_card}):\n{hand_data.river_action}"
    
    # Get current street
    street = hand_data.get_street()
    
    # Replace template variables
    prompt = template.replace("{{street}}", street)
    prompt = prompt.replace("{{table_type}}", hand_data.table_type.value)
    prompt = prompt.replace("{{effective_stack_bb}}", str(hand_data.effective_stack_bb))
    prompt = prompt.replace("{{hero_position}}", hand_data.hero_position.value)
    prompt = prompt.replace("{{hero_hand}}", hand_data.hero_hand)
    prompt = prompt.replace("{{villain_positions}}", ', '.join(v.value for v in hand_data.villain_positions))
    prompt = prompt.replace("{{preflop_action}}", hand_data.preflop_action)
    prompt = prompt.replace("{{flop_board}}", ' '.join(hand_data.flop_board))
    prompt = prompt.replace("{{flop_action}}", hand_data.flop_action)
    prompt = prompt.replace("{{turn_section}}", turn_section)
    prompt = prompt.replace("{{river_section}}", river_section)
    
    return prompt


def _construct_exploitative_with_notes_prompt(hand_data: PokerHandSchema) -> str:
    """
    Construct exploitative analysis with specific villain notes using template file.
    """
    # Load the exploitative_with_notes template
    template = load_prompt_template("exploitative_with_notes")
    
    # Build turn section if turn card exists
    turn_section = ""
    if hand_data.turn_card:
        turn_section = f"\n\nTURN ({hand_data.turn_card}):\n{hand_data.turn_action}"
    
    # Build river section if river card exists
    river_section = ""
    if hand_data.river_card:
        river_section = f"\n\nRIVER ({hand_data.river_card}):\n{hand_data.river_action}"
    
    # Get current street
    street = hand_data.get_street()
    
    # Replace template variables
    prompt = template.replace("{{street}}", street)
    prompt = prompt.replace("{{table_type}}", hand_data.table_type.value)
    prompt = prompt.replace("{{effective_stack_bb}}", str(hand_data.effective_stack_bb))
    prompt = prompt.replace("{{hero_position}}", hand_data.hero_position.value)
    prompt = prompt.replace("{{hero_hand}}", hand_data.hero_hand)
    prompt = prompt.replace("{{villain_positions}}", ', '.join(v.value for v in hand_data.villain_positions))
    prompt = prompt.replace("{{preflop_action}}", hand_data.preflop_action)
    prompt = prompt.replace("{{flop_board}}", ' '.join(hand_data.flop_board))
    prompt = prompt.replace("{{flop_action}}", hand_data.flop_action)
    prompt = prompt.replace("{{turn_section}}", turn_section)
    prompt = prompt.replace("{{river_section}}", river_section)
    prompt = prompt.replace("{{villain_notes}}", hand_data.villain_notes or "")
    
    return prompt


def _construct_review_prompt(hand_data: PokerHandSchema) -> str:
    """
    Construct comprehensive hand review prompt using template file.
    """
    # Load the review template
    template = load_prompt_template("review")
    
    # Build turn section if turn card exists
    turn_section = ""
    if hand_data.turn_card:
        turn_section = f"\n\nTURN ({hand_data.turn_card}):\n{hand_data.turn_action}"
    
    # Build river section if river card exists
    river_section = ""
    if hand_data.river_card:
        river_section = f"\n\nRIVER ({hand_data.river_card}):\n{hand_data.river_action}"
    
    # Get current street
    street = hand_data.get_street()
    
    # Replace template variables
    prompt = template.replace("{{street}}", street)
    prompt = prompt.replace("{{table_type}}", hand_data.table_type.value)
    prompt = prompt.replace("{{effective_stack_bb}}", str(hand_data.effective_stack_bb))
    prompt = prompt.replace("{{hero_position}}", hand_data.hero_position.value)
    prompt = prompt.replace("{{hero_hand}}", hand_data.hero_hand)
    prompt = prompt.replace("{{villain_positions}}", ', '.join(v.value for v in hand_data.villain_positions))
    prompt = prompt.replace("{{preflop_action}}", hand_data.preflop_action)
    prompt = prompt.replace("{{flop_board}}", ' '.join(hand_data.flop_board))
    prompt = prompt.replace("{{flop_action}}", hand_data.flop_action)
    prompt = prompt.replace("{{turn_section}}", turn_section)
    prompt = prompt.replace("{{river_section}}", river_section)
    
    return prompt

@router.post("/chat/hand")
async def chat_about_hand(request: ChatMessageRequest):
    """
    Chat endpoint for hand-scoped follow-up questions.
    
    This endpoint allows users to ask questions about a specific analyzed hand.
    The hand context is immutable and all responses stay within that context.
    
    IMPORTANT: The LLM is instructed to ONLY answer questions about the specific hand
    provided in hand_context. It must not introduce new facts or reference other hands.
    
    Parameters:
    - hand_id: Unique identifier for the hand
    - message: User's question about the hand
    - hand_context: Complete immutable hand context
    
    Returns:
    - Focused answer about the specific hand from the LLM
    """
    
    # Build board string
    board_parts = []
    flop_cards = request.hand_context.board.get("flop", [])
    turn_card = request.hand_context.board.get("turn")
    river_card = request.hand_context.board.get("river")
    
    if flop_cards:
        board_parts.append(f"Flop: {' '.join(flop_cards)}")
    if turn_card:
        board_parts.append(f"Turn: {turn_card}")
    if river_card:
        board_parts.append(f"River: {river_card}")
    
    board_str = ", ".join(board_parts)
    
    # Construct hand-scoped prompt
    prompt = f"""You are a poker coach answering a follow-up question about a SPECIFIC hand that has already been analyzed.

CRITICAL INSTRUCTIONS:
- ONLY answer questions about THIS specific hand
- DO NOT introduce new facts or scenarios
- DO NOT reference other hands or situations
- Stay strictly within the provided hand context
- If the question is unrelated to this hand, politely redirect to the hand context

HAND CONTEXT (IMMUTABLE):
Hand ID: {request.hand_context.hand_id}
Game: {request.hand_context.game_type}
Stack: {request.hand_context.stack_depth}
Position: {request.hand_context.hero_position}
Hero Hand: {request.hand_context.hero_hand}
Board: {board_str}
Analysis Mode: {request.hand_context.analysis_mode}"""

    if request.hand_context.range_preset:
        prompt += f"\nRange Preset: {request.hand_context.range_preset}"
    
    if request.hand_context.villain_notes:
        prompt += f"\nVillain Notes: {request.hand_context.villain_notes}"
    
    prompt += f"""

ACTION SEQUENCE:
{request.hand_context.actions}

USER'S QUESTION:
{request.message}

Provide a clear, concise answer focused ONLY on this specific hand. Keep your response educational and helpful."""

    try:
        # Send to LLM
        llm_response = await ollama_client.analyze_hand(prompt)
        
        return {
            "hand_id": request.hand_id,
            "question": request.message,
            "answer": llm_response,
            "analysis_mode": request.hand_context.analysis_mode
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Chat service error: {str(e)}"
        )
