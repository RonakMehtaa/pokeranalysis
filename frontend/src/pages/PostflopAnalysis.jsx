import { useState } from 'react';
import '../App.css';

const PostflopAnalysis = () => {
  const [formData, setFormData] = useState({
    position: '',
    heroCards: '',
    boardCards: '',
    actions: '',
    villainNotes: '',
    tableType: '6max',
    effectiveStack: '100',
    villainPositions: ''
  });
  
  const [activeTab, setActiveTab] = useState('gto');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);

  const positions = ['UTG', 'UTG+1', 'UTG+2', 'MP', 'MP+1', 'CO', 'BTN', 'SB', 'BB'];
  const ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2'];
  const suits = ['♠', '♥', '♦', '♣'];

  const [heroCardSelector, setHeroCardSelector] = useState({ show: false, cardIndex: 0 });
  const [boardCardSelector, setBoardCardSelector] = useState({ show: false, cardIndex: 0 });

  const handlePositionChange = (pos) => {
    setFormData({ ...formData, position: pos });
  };

  const handleCardSelect = (rank, suit, type, index) => {
    const card = `${rank}${suit}`;
    
    if (type === 'hero') {
      const cards = formData.heroCards.split(' ').filter(c => c);
      if (cards.length < 2 || index < cards.length) {
        cards[index] = card;
        setFormData({ ...formData, heroCards: cards.join(' ') });
      }
      setHeroCardSelector({ show: false, cardIndex: 0 });
    } else if (type === 'board') {
      const cards = formData.boardCards.split(' ').filter(c => c);
      if (cards.length < 5 || index < cards.length) {
        cards[index] = card;
        setFormData({ ...formData, boardCards: cards.join(' ') });
      }
      setBoardCardSelector({ show: false, cardIndex: 0 });
    }
  };

  const openCardPicker = (type, index) => {
    if (type === 'hero') {
      setHeroCardSelector({ show: true, cardIndex: index });
    } else {
      setBoardCardSelector({ show: true, cardIndex: index });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    console.log('=== FORM SUBMISSION STARTED ===');
    console.log('Form Data:', formData);
    console.log('Active Tab:', activeTab);
    
    // Validation
    if (!formData.position) {
      console.error('Validation failed: No position selected');
      setError('Please select a position');
      return;
    }
    if (!formData.heroCards || formData.heroCards.split(' ').filter(c => c).length !== 2) {
      console.error('Validation failed: Invalid hero cards', formData.heroCards);
      setError('Please select exactly 2 hero cards');
      return;
    }
    if (!formData.boardCards || formData.boardCards.split(' ').filter(c => c).length < 3) {
      console.error('Validation failed: Invalid board cards', formData.boardCards);
      setError('Please select at least 3 board cards (flop)');
      return;
    }
    if (!formData.actions.trim()) {
      console.error('Validation failed: No actions provided');
      setError('Please describe the actions');
      return;
    }
    if (!formData.villainPositions.trim()) {
      console.error('Validation failed: No villain positions');
      setError('Please specify villain positions (e.g., BB or SB,BB)');
      return;
    }

    console.log('✓ All validations passed');
    
    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const boardCardsArray = formData.boardCards.split(' ').filter(c => c);
      const heroCardsArray = formData.heroCards.split(' ').filter(c => c);
      
      console.log('Board Cards Array:', boardCardsArray);
      console.log('Hero Cards Array:', heroCardsArray);
      
      // Convert hero cards to proper notation (e.g., "A♠ K♥" -> "AKo" or "AKs")
      const heroHandNotation = convertCardsToNotation(heroCardsArray);
      console.log('Hero Hand Notation:', heroHandNotation);
      
      // Convert board cards to backend format (e.g., "A♠" -> "As")
      const flopBoard = boardCardsArray.slice(0, 3).map(convertCardNotation);
      const turnCard = boardCardsArray[3] ? convertCardNotation(boardCardsArray[3]) : null;
      const riverCard = boardCardsArray[4] ? convertCardNotation(boardCardsArray[4]) : null;
      
      console.log('Flop Board:', flopBoard);
      console.log('Turn Card:', turnCard);
      console.log('River Card:', riverCard);
      
      // Parse villain positions
      const villainPositions = formData.villainPositions.split(',').map(p => p.trim());
      console.log('Villain Positions:', villainPositions);
      
      // Build the hand_data object according to PokerHandSchema
      const handData = {
        table_type: formData.tableType,
        effective_stack_bb: parseFloat(formData.effectiveStack),
        hero_position: formData.position,
        hero_hand: heroHandNotation,
        villain_positions: villainPositions,
        preflop_action: "Folds to hero",
        flop_board: flopBoard,
        flop_action: formData.actions,
      };

      // Only add turn/river if they exist
      if (turnCard) {
        handData.turn_card = turnCard;
        handData.turn_action = "Continued action (see action sequence)";
      }
      
      if (riverCard) {
        handData.river_card = riverCard;
        handData.river_action = "Continued action (see action sequence)";
      }
      
      if (formData.villainNotes) {
        handData.villain_notes = formData.villainNotes;
      }

      console.log('=== REQUEST PAYLOAD ===');
      console.log('Hand Data:', JSON.stringify(handData, null, 2));
      
      const apiUrl = `http://localhost:8000/api/analyze/postflop?analysis_type=${activeTab}`;
      console.log('API URL:', apiUrl);
      console.log('Method: POST');
      console.log('Headers:', { 'Content-Type': 'application/json' });

      console.log('Sending fetch request...');
      const res = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(handData),
      });

      console.log('Response received');
      console.log('Response status:', res.status);
      console.log('Response ok?:', res.ok);
      console.log('Response headers:', Object.fromEntries(res.headers.entries()));

      if (!res.ok) {
        console.error('Response not OK, attempting to parse error');
        const errorData = await res.json().catch(() => ({ detail: 'Unknown error' }));
        console.error('Error data:', errorData);
        throw new Error(errorData.detail || `Server error: ${res.status}`);
      }

      console.log('Parsing successful response...');
      const data = await res.json();
      console.log('=== RESPONSE DATA ===');
      console.log('Response:', data);
      console.log('Analysis:', data.analysis);
      
      setResponse(data.analysis);
      console.log('✓ Analysis set successfully');
    } catch (err) {
      console.error('=== ERROR CAUGHT ===');
      console.error('Error type:', err.constructor.name);
      console.error('Error message:', err.message);
      console.error('Error stack:', err.stack);
      console.error('Full error:', err);
      setError(err.message || 'Failed to get analysis. Make sure the backend is running.');
    } finally {
      setLoading(false);
      console.log('=== FORM SUBMISSION ENDED ===');
    }
  };

  // Helper function to convert cards to hand notation
  const convertCardsToNotation = (cards) => {
    if (cards.length !== 2) return '';
    
    const rankOrder = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2'];
    const suitSymbols = { '♠': 's', '♥': 'h', '♦': 'd', '♣': 'c' };
    
    const card1 = { rank: cards[0][0], suit: suitSymbols[cards[0][1]] };
    const card2 = { rank: cards[1][0], suit: suitSymbols[cards[1][1]] };
    
    // Pocket pair
    if (card1.rank === card2.rank) {
      return card1.rank + card1.rank;
    }
    
    // Order by rank (higher first)
    const rank1Idx = rankOrder.indexOf(card1.rank);
    const rank2Idx = rankOrder.indexOf(card2.rank);
    
    let highRank, lowRank;
    let suited;
    
    if (rank1Idx < rank2Idx) {
      highRank = card1.rank;
      lowRank = card2.rank;
      suited = card1.suit === card2.suit;
    } else {
      highRank = card2.rank;
      lowRank = card1.rank;
      suited = card1.suit === card2.suit;
    }
    
    return highRank + lowRank + (suited ? 's' : 'o');
  };

  // Helper function to convert card notation
  const convertCardNotation = (card) => {
    const suitSymbols = { '♠': 's', '♥': 'h', '♦': 'd', '♣': 'c' };
    return card[0] + suitSymbols[card[1]];
  };

  const clearHeroCards = () => {
    setFormData({ ...formData, heroCards: '' });
  };

  const clearBoardCards = () => {
    setFormData({ ...formData, boardCards: '' });
  };

  const formatResponse = (text) => {
    if (!text) return null;
    
    // Split by double newlines to create paragraphs
    const sections = text.split('\n\n').filter(s => s.trim());
    
    return sections.map((section, idx) => {
      const lines = section.split('\n');
      return (
        <div key={idx} className="response-section">
          {lines.map((line, lineIdx) => {
            // Check if line is a header (starts with ## or **...:**)
            if (line.startsWith('##')) {
              return <h3 key={lineIdx} className="response-header">{line.replace(/^##\s*/, '')}</h3>;
            } else if (line.match(/^\*\*.*:\*\*/)) {
              return <h4 key={lineIdx} className="response-subheader">{line.replace(/\*\*/g, '')}</h4>;
            } else if (line.startsWith('- ')) {
              return <li key={lineIdx} className="response-list-item">{line.substring(2)}</li>;
            } else if (line.trim()) {
              return <p key={lineIdx} className="response-text">{line}</p>;
            }
            return null;
          })}
        </div>
      );
    });
  };

  const heroCardsArray = formData.heroCards.split(' ').filter(c => c);
  const boardCardsArray = formData.boardCards.split(' ').filter(c => c);

  return (
    <div className="page postflop-analysis">
      <h1>Postflop Analysis</h1>
      <p className="subtitle">
        Analyze specific postflop situations with detailed strategy advice
      </p>

      {/* Tabs for analysis type */}
      <div className="controls">
        <div className="tabs" role="tablist" aria-label="Analysis Type">
          {['gto','exploitative','review'].map((tab) => (
            <button
              key={tab}
              type="button"
              role="tab"
              aria-selected={activeTab === tab}
              className={`tab ${activeTab === tab ? 'active' : ''}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab === 'gto' ? 'GTO' : tab === 'exploitative' ? 'Exploitative' : 'Review'}
            </button>
          ))}
        </div>
      </div>

      <div className="controls postflop-form">
        <form onSubmit={handleSubmit}>
          {/* Position Selection */}
          <div className="control-group">
            <label>Position</label>
            <div className="button-group position-group">
              {positions.map((pos) => (
                <button
                  key={pos}
                  type="button"
                  className={formData.position === pos ? 'active' : ''}
                  onClick={() => handlePositionChange(pos)}
                >
                  {pos}
                </button>
              ))}
            </div>
          </div>

          {/* Table Type and Stack Size */}
          <div className="control-group">
            <label>Table Type</label>
            <div className="button-group">
              <button
                type="button"
                className={formData.tableType === '6max' ? 'active' : ''}
                onClick={() => setFormData({ ...formData, tableType: '6max' })}
              >
                6-Max
              </button>
              <button
                type="button"
                className={formData.tableType === '9max' ? 'active' : ''}
                onClick={() => setFormData({ ...formData, tableType: '9max' })}
              >
                9-Max
              </button>
            </div>
          </div>

          <div className="control-group">
            <label>Effective Stack (BB)</label>
            <input
              type="number"
              className="input-field stack-input"
              placeholder="100"
              value={formData.effectiveStack}
              onChange={(e) => setFormData({ ...formData, effectiveStack: e.target.value })}
              min="1"
              step="0.1"
            />
          </div>

          <div className="control-group">
            <label>Villain Positions</label>
            <input
              type="text"
              className="input-field"
              placeholder="e.g., BB or SB,BB"
              value={formData.villainPositions}
              onChange={(e) => setFormData({ ...formData, villainPositions: e.target.value })}
            />
            <small style={{ color: '#888', fontSize: '0.85em', marginTop: '4px' }}>
              Enter comma-separated positions (e.g., "BB" or "SB,BB")
            </small>
          </div>

          {/* Hero Cards */}
          <div className="control-group">
            <label>Hero Cards</label>
            <div className="card-input-container">
              <div className="card-display">
                {[0, 1].map((index) => (
                  <button
                    key={index}
                    type="button"
                    className="card-slot"
                    onClick={() => openCardPicker('hero', index)}
                  >
                    {heroCardsArray[index] || '+'}
                  </button>
                ))}
                {heroCardsArray.length > 0 && (
                  <button type="button" className="clear-btn" onClick={clearHeroCards}>
                    Clear
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Hero Card Picker */}
          {heroCardSelector.show && (
            <div className="card-picker-overlay" onClick={() => setHeroCardSelector({ show: false, cardIndex: 0 })}>
              <div className="card-picker" onClick={(e) => e.stopPropagation()}>
                <h3>Select Card {heroCardSelector.cardIndex + 1}</h3>
                <div className="card-grid">
                  {ranks.map((rank) => (
                    <div key={rank} className="rank-row">
                      {suits.map((suit) => (
                        <button
                          key={`${rank}${suit}`}
                          type="button"
                          className={`card-option ${suit === '♥' || suit === '♦' ? 'red' : 'black'}`}
                          onClick={() => handleCardSelect(rank, suit, 'hero', heroCardSelector.cardIndex)}
                        >
                          {rank}{suit}
                        </button>
                      ))}
                    </div>
                  ))}
                </div>
                <button 
                  type="button" 
                  className="close-picker"
                  onClick={() => setHeroCardSelector({ show: false, cardIndex: 0 })}
                >
                  Close
                </button>
              </div>
            </div>
          )}

          {/* Board Cards */}
          <div className="control-group">
            <label>Board Cards</label>
            <div className="card-input-container">
              <div className="card-display">
                {[0, 1, 2, 3, 4].map((index) => (
                  <button
                    key={index}
                    type="button"
                    className="card-slot"
                    onClick={() => openCardPicker('board', index)}
                  >
                    {boardCardsArray[index] || '+'}
                  </button>
                ))}
                {boardCardsArray.length > 0 && (
                  <button type="button" className="clear-btn" onClick={clearBoardCards}>
                    Clear
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Board Card Picker */}
          {boardCardSelector.show && (
            <div className="card-picker-overlay" onClick={() => setBoardCardSelector({ show: false, cardIndex: 0 })}>
              <div className="card-picker" onClick={(e) => e.stopPropagation()}>
                <h3>Select Board Card {boardCardSelector.cardIndex + 1}</h3>
                <div className="card-grid">
                  {ranks.map((rank) => (
                    <div key={rank} className="rank-row">
                      {suits.map((suit) => (
                        <button
                          key={`${rank}${suit}`}
                          type="button"
                          className={`card-option ${suit === '♥' || suit === '♦' ? 'red' : 'black'}`}
                          onClick={() => handleCardSelect(rank, suit, 'board', boardCardSelector.cardIndex)}
                        >
                          {rank}{suit}
                        </button>
                      ))}
                    </div>
                  ))}
                </div>
                <button 
                  type="button" 
                  className="close-picker"
                  onClick={() => setBoardCardSelector({ show: false, cardIndex: 0 })}
                >
                  Close
                </button>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="control-group">
            <label>Action Sequence</label>
            <textarea
              className="action-textarea"
              placeholder="Describe the action sequence (e.g., 'Hero checks, Villain bets 50% pot, Hero calls')"
              value={formData.actions}
              onChange={(e) => setFormData({ ...formData, actions: e.target.value })}
              rows={4}
            />
          </div>

          {/* Villain Notes */}
          <div className="control-group">
            <label>Villain Notes (Optional)</label>
            <textarea
              className="action-textarea"
              placeholder="Add any relevant notes about villain's tendencies..."
              value={formData.villainNotes}
              onChange={(e) => setFormData({ ...formData, villainNotes: e.target.value })}
              rows={3}
            />
          </div>

          <button className="submit-btn" type="submit" disabled={loading}>
            {loading ? 'Analyzing…' : 'Analyze Hand'}
          </button>
        </form>
      </div>

      {/* Feedback and Results */}
      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      <div className={`result-area ${response ? 'result-filled' : ''}`}>
        {loading && <div className="loading">Processing your hand…</div>}
        {!loading && response && (
          <div className="response-container">
            <h2>Analysis Result</h2>
            <div className="response-content">{formatResponse(response)}</div>
          </div>
        )}
        {!loading && !response && !error && (
          <div className="loading">Submit a hand to see analysis here.</div>
        )}
      </div>
    </div>
  );
};

export default PostflopAnalysis;
