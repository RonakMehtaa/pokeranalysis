"""
API Routes for Poker Learning App

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
from models import PokerHandSchema, HandAnalysisRequest, PreflopDecisionRequest, LLMAnalysisRequest
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
    prompt = f"""You are a poker learning assistant. Analyze the following hand based on the provided range data.

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
    Construct GTO-focused analysis prompt.
    Focuses on balanced, game-theory optimal play.
    """
    board = " ".join(hand_data.get_board())
    street = hand_data.get_street()
    
    prompt = f"""You are an expert poker coach specializing in Game Theory Optimal (GTO) strategy.

Analyze this {street} decision from a GTO perspective:

HAND DETAILS:
Table: {hand_data.table_type.value}
Effective Stack: {hand_data.effective_stack_bb}bb
Hero Position: {hand_data.hero_position.value}
Hero Hand: {hand_data.hero_hand}
Villains: {', '.join(v.value for v in hand_data.villain_positions)}

PREFLOP:
{hand_data.preflop_action}

FLOP ({' '.join(hand_data.flop_board)}):
{hand_data.flop_action}"""

    if hand_data.turn_card:
        prompt += f"""

TURN ({hand_data.turn_card}):
{hand_data.turn_action}"""

    if hand_data.river_card:
        prompt += f"""

RIVER ({hand_data.river_card}):
{hand_data.river_action}"""

    prompt += f"""

PROVIDE GTO ANALYSIS:

1. RANGE ANALYSIS
   - What does Hero's range look like on this {street}?
   - What does Villain's range look like on this {street}?
   - How does this specific hand ({hand_data.hero_hand}) fit into Hero's range?

2. BOARD TEXTURE
   - Analyze the board texture: {board}
   - Which range benefits from this texture?
   - What are the key equity considerations?

3. OPTIMAL STRATEGY
   - What is the GTO-recommended action on this {street}?
   - What bet sizing should be used (if betting/raising)?
   - How should this hand be balanced within the overall strategy?

4. FREQUENCY CONSIDERATIONS
   - At what frequency should Hero take each action?
   - What hands should be mixed in similar spots?
   - How does this prevent exploitation?

5. KEY LEARNING POINTS
   - What GTO principles apply to this hand?
   - Common mistakes players make in this spot
   - How this hand performs in the overall strategy

Keep the analysis focused on balanced, unexploitable play. Use percentages and frequencies where applicable."""

    return prompt


def _construct_exploitative_prompt(hand_data: PokerHandSchema) -> str:
    """
    Construct exploitative analysis prompt.
    Focuses on adjustments based on common opponent tendencies.
    """
    board = " ".join(hand_data.get_board())
    street = hand_data.get_street()
    
    prompt = f"""You are an expert poker coach specializing in exploitative strategy and opponent tendencies.

Analyze this {street} decision with an exploitative approach:

HAND DETAILS:
Table: {hand_data.table_type.value}
Effective Stack: {hand_data.effective_stack_bb}bb
Hero Position: {hand_data.hero_position.value}
Hero Hand: {hand_data.hero_hand}
Villains: {', '.join(v.value for v in hand_data.villain_positions)}

PREFLOP:
{hand_data.preflop_action}

FLOP ({' '.join(hand_data.flop_board)}):
{hand_data.flop_action}"""

    if hand_data.turn_card:
        prompt += f"""

TURN ({hand_data.turn_card}):
{hand_data.turn_action}"""

    if hand_data.river_card:
        prompt += f"""

RIVER ({hand_data.river_card}):
{hand_data.river_action}"""

    prompt += f"""

PROVIDE EXPLOITATIVE ANALYSIS:

1. OPPONENT TENDENCIES TO CONSIDER
   - What common mistakes do opponents make in this spot?
   - How do typical players at this level misplay this situation?
   - What population tendencies can be exploited?

2. EXPLOITATIVE ADJUSTMENTS
   - Against a TIGHT/PASSIVE opponent: What's the best line?
   - Against an AGGRESSIVE/LOOSE opponent: What's the best line?
   - Against a CALLING STATION: What's the best line?
   - Against a TIGHT/AGGRESSIVE opponent: What's the best line?

3. ACTION RECOMMENDATION
   - What is the most exploitative play on this {street}?
   - How should bet sizing be adjusted to maximize EV?
   - What future streets should be considered?

4. HAND READING
   - Based on the action, what hands is Villain likely to have?
   - What hands would Villain play differently?
   - How does this narrow their range?

5. MAXIMIZING VALUE/MINIMIZING LOSS
   - How can we extract maximum value with this hand?
   - What are the key decision points?
   - Common timing tells or bet sizing tells to watch for

Focus on practical, exploitative adjustments that maximize profit against imperfect opponents."""

    return prompt


def _construct_exploitative_with_notes_prompt(hand_data: PokerHandSchema) -> str:
    """
    Construct exploitative analysis with specific villain notes.
    Uses the villain_notes field for targeted exploitation.
    """
    board = " ".join(hand_data.get_board())
    street = hand_data.get_street()
    
    prompt = f"""You are an expert poker coach specializing in exploitative play against specific opponent tendencies.

Analyze this {street} decision with focus on exploiting THIS specific opponent:

HAND DETAILS:
Table: {hand_data.table_type.value}
Effective Stack: {hand_data.effective_stack_bb}bb
Hero Position: {hand_data.hero_position.value}
Hero Hand: {hand_data.hero_hand}
Villains: {', '.join(v.value for v in hand_data.villain_positions)}

VILLAIN NOTES/READS:
{hand_data.villain_notes}

PREFLOP:
{hand_data.preflop_action}

FLOP ({' '.join(hand_data.flop_board)}):
{hand_data.flop_action}"""

    if hand_data.turn_card:
        prompt += f"""

TURN ({hand_data.turn_card}):
{hand_data.turn_action}"""

    if hand_data.river_card:
        prompt += f"""

RIVER ({hand_data.river_card}):
{hand_data.river_action}"""

    prompt += f"""

PROVIDE TARGETED EXPLOITATIVE ANALYSIS:

1. VILLAIN-SPECIFIC READ
   - How do the notes/reads affect this specific situation?
   - What patterns has Villain shown that are relevant here?
   - What is Villain's most likely hand range based on their tendencies?

2. OPTIMAL EXPLOITATION STRATEGY
   - Given these specific reads, what is the best action on this {street}?
   - How should sizing be adjusted to exploit Villain's tendencies?
   - What future streets need to be considered based on Villain's profile?

3. DECISION TREE
   - If Hero takes action X, how is Villain likely to respond?
   - What backup plans are needed if Villain deviates?
   - How can we maximize EV against THIS player?

4. RISK ASSESSMENT
   - What are the risks of this exploitative play?
   - Could Villain be leveling/trapping?
   - When should we revert to more balanced play?

5. ADJUSTMENTS FOR FUTURE HANDS
   - How might Villain adjust if we exploit them this way?
   - What notes should we continue to gather?
   - When to change our exploitation strategy?

Focus heavily on the specific villain notes provided and how they create profitable exploits in this exact situation."""

    return prompt


def _construct_review_prompt(hand_data: PokerHandSchema) -> str:
    """
    Construct comprehensive hand review prompt.
    Covers multiple perspectives and learning points.
    """
    board = " ".join(hand_data.get_board())
    street = hand_data.get_street()
    
    prompt = f"""You are an expert poker coach conducting a comprehensive hand review.

Review this complete hand with focus on learning and improvement:

HAND DETAILS:
Table: {hand_data.table_type.value}
Effective Stack: {hand_data.effective_stack_bb}bb
Hero Position: {hand_data.hero_position.value}
Hero Hand: {hand_data.hero_hand}
Villains: {', '.join(v.value for v in hand_data.villain_positions)}

COMPLETE HAND HISTORY:

PREFLOP:
{hand_data.preflop_action}

FLOP ({' '.join(hand_data.flop_board)}):
{hand_data.flop_action}"""

    if hand_data.turn_card:
        prompt += f"""

TURN ({hand_data.turn_card}):
{hand_data.turn_action}"""

    if hand_data.river_card:
        prompt += f"""

RIVER ({hand_data.river_card}):
{hand_data.river_action}"""

    if hand_data.villain_notes:
        prompt += f"""

VILLAIN NOTES:
{hand_data.villain_notes}"""

    prompt += f"""

PROVIDE COMPREHENSIVE HAND REVIEW:

1. PREFLOP ANALYSIS
   - Was the preflop action standard?
   - Any concerns with the preflop play?
   - Position and range considerations

2. STREET-BY-STREET BREAKDOWN
   - Analyze each street's decision
   - Was the action taken optimal?
   - What alternatives should have been considered?
   - Critical decision points

3. MULTIPLE PERSPECTIVES
   - GTO perspective: What does solver strategy suggest?
   - Exploitative perspective: How could opponent tendencies be exploited?
   - Risk management: Was variance handled appropriately?

4. HAND STRENGTH THROUGHOUT
   - How did hand strength change on each street?
   - When was Hero ahead/behind?
   - Equity considerations and how they evolved

5. ALTERNATIVE LINES
   - What other lines could have been taken?
   - Compare EV of different approaches
   - Which line is best and why?

6. KEY LESSONS
   - What are the main takeaways from this hand?
   - What concepts does this hand teach?
   - How to recognize similar spots in the future?
   - Common mistakes to avoid

7. OVERALL ASSESSMENT
   - Grade the play (A+ to F)
   - Biggest mistake (if any)
   - Best decision made
   - Summary and final thoughts

Be thorough, educational, and honest in the review. Focus on helping the player improve."""

    return prompt
