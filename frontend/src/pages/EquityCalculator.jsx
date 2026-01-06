import { useState, useRef, useEffect } from 'react';
import './EquityCalculator.css';

// Simple in-memory cache for equity calculations
const equityCache = new Map();

const EquityCalculator = () => {
  const [players, setPlayers] = useState([
    { id: '1', name: 'Hero', holeCards: [] },
    { id: '2', name: 'Villain', holeCards: [] }
  ]);
  const [boardCards, setBoardCards] = useState([]);
  const [iterations, setIterations] = useState(20000);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedPlayer, setSelectedPlayer] = useState(null);
  const [selectingBoard, setSelectingBoard] = useState(false);
  const [showTooltip, setShowTooltip] = useState(null);
  const [cacheHit, setCacheHit] = useState(false);
  const tooltipTimeoutRef = useRef(null);

  const resultsRef = useRef(null);

  const ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2'];
  const suits = [
    { symbol: '♠', code: 's', color: 'black' },
    { symbol: '♥', code: 'h', color: 'red' },
    { symbol: '♦', code: 'd', color: 'red' },
    { symbol: '♣', code: 'c', color: 'black' }
  ];

  // Tooltips data
  const tooltips = {
    equity: {
      title: "Equity %",
      description: "Your share of the pot on average. Calculated as: Win% + (Tie% ÷ Number of Players in Tie)"
    },
    win: {
      title: "Win %",
      description: "Percentage of times you have the best hand outright (no ties)"
    },
    tie: {
      title: "Tie %",
      description: "Percentage of times you split the pot with one or more players"
    }
  };

  // Tooltip handlers with delay to prevent flickering
  const handleTooltipEnter = (tooltipType) => {
    if (tooltipTimeoutRef.current) {
      clearTimeout(tooltipTimeoutRef.current);
    }
    setShowTooltip(tooltipType);
  };

  const handleTooltipLeave = () => {
    tooltipTimeoutRef.current = setTimeout(() => {
      setShowTooltip(null);
    }, 100);
  };

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (tooltipTimeoutRef.current) {
        clearTimeout(tooltipTimeoutRef.current);
      }
    };
  }, []);

  // Get all used cards
  const getUsedCards = () => {
    const used = new Set();
    players.forEach(player => {
      player.holeCards.forEach(card => used.add(card));
    });
    boardCards.forEach(card => used.add(card));
    return used;
  };

  // Check if a card is available
  const isCardAvailable = (card) => {
    return !getUsedCards().has(card);
  };

  // Add a player
  const addPlayer = () => {
    if (players.length < 6) {
      const newId = (Math.max(...players.map(p => parseInt(p.id))) + 1).toString();
      setPlayers([...players, { 
        id: newId, 
        name: `Player ${newId}`, 
        holeCards: [] 
      }]);
    }
  };

  // Remove a player
  const removePlayer = (playerId) => {
    if (players.length > 2) {
      setPlayers(players.filter(p => p.id !== playerId));
    }
  };

  // Update player name
  const updatePlayerName = (playerId, name) => {
    setPlayers(players.map(p => 
      p.id === playerId ? { ...p, name } : p
    ));
  };

  // Select a card for player hole cards
  const selectPlayerCard = (playerId, card) => {
    setPlayers(players.map(p => {
      if (p.id === playerId) {
        if (p.holeCards.includes(card)) {
          // Deselect card
          return { ...p, holeCards: p.holeCards.filter(c => c !== card) };
        } else if (p.holeCards.length < 2) {
          // Add card
          return { ...p, holeCards: [...p.holeCards, card] };
        }
      }
      return p;
    }));
  };

  // Select a card for board
  const selectBoardCard = (card) => {
    if (boardCards.includes(card)) {
      // Deselect card
      setBoardCards(boardCards.filter(c => c !== card));
    } else if (boardCards.length < 5) {
      // Add card
      setBoardCards([...boardCards, card]);
    }
  };

  // Clear player hole cards
  const clearPlayerCards = (playerId) => {
    setPlayers(players.map(p => 
      p.id === playerId ? { ...p, holeCards: [] } : p
    ));
  };

  // Clear board cards
  const clearBoard = () => {
    setBoardCards([]);
  };

  // Validate input
  const isInputValid = () => {
    // All players must have exactly 2 hole cards
    const allPlayersHaveCards = players.every(p => p.holeCards.length === 2);
    return allPlayersHaveCards;
  };

  // Generate cache key from current state
  const generateCacheKey = (playersData, board, iters) => {
    const sortedPlayers = playersData
      .map(p => ({
        cards: [...p.holeCards].sort().join(',')
      }))
      .sort((a, b) => a.cards.localeCompare(b.cards));
    
    const sortedBoard = [...board].sort().join(',');
    return `${JSON.stringify(sortedPlayers)}|${sortedBoard}|${iters}`;
  };

  // Check if we have cached results
  const getCachedResult = (key) => {
    return equityCache.get(key);
  };

  // Store result in cache
  const setCachedResult = (key, result) => {
    // Limit cache size to prevent memory issues
    if (equityCache.size > 50) {
      const firstKey = equityCache.keys().next().value;
      equityCache.delete(firstKey);
    }
    equityCache.set(key, result);
  };

  // Calculate equity with caching
  const calculateEquity = async () => {
    if (!isInputValid()) return;

    // Generate cache key
    const cacheKey = generateCacheKey(players, boardCards, iterations);
    
    // Check cache first
    const cached = getCachedResult(cacheKey);
    if (cached) {
      setResults(cached);
      setCacheHit(true);
      setTimeout(() => setCacheHit(false), 2000);
      // Auto-scroll to results
      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);
    setCacheHit(false);

    try {
      const response = await fetch('http://localhost:8000/api/equity/calculate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          players: players.map(p => ({
            id: p.name,
            hole_cards: p.holeCards
          })),
          board_cards: boardCards.length > 0 ? boardCards : null,
          iterations: iterations
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to calculate equity');
      }

      const data = await response.json();
      
      // Cache the result
      setCachedResult(cacheKey, data);
      
      setResults(data);
      
      // Auto-scroll to results after they're rendered
      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Get estimated calculation time
  const getEstimatedTime = (iters) => {
    if (iters <= 5000) return 'Fast (~1s)';
    if (iters <= 10000) return 'Quick (~2s)';
    if (iters <= 20000) return 'Normal (~4s)';
    if (iters <= 50000) return 'Slower (~8s)';
    return 'Slow (~15s)';
  };

  // Format card display
  const formatCard = (card) => {
    const rank = card[0];
    const suitCode = card[1];
    const suit = suits.find(s => s.code === suitCode);
    return { rank, suit };
  };

  // Get highest equity player
  const getHighestEquityPlayer = () => {
    if (!results) return null;
    let maxEquity = -1;
    let maxPlayer = null;
    Object.entries(results.players).forEach(([name, data]) => {
      if (data.equity_percentage > maxEquity) {
        maxEquity = data.equity_percentage;
        maxPlayer = name;
      }
    });
    return maxPlayer;
  };

  return (
    <div className="equity-calculator">
      <h1>Equity Calculator</h1>
      
      {/* Players Section - Compact Grid Layout */}
      <div className="players-section">
        <div className="section-header">
          <h2>Players ({players.length}/6)</h2>
          <button 
            onClick={addPlayer} 
            disabled={players.length >= 6}
            className="add-player-btn"
          >
            + Add Player
          </button>
        </div>

        <div className="players-grid">
          {players.map((player) => (
            <div key={player.id} className="player-card-compact">
              <div className="player-header-compact">
                <input
                  type="text"
                  value={player.name}
                  onChange={(e) => updatePlayerName(player.id, e.target.value)}
                  className="player-name-input-compact"
                  placeholder="Player name"
                />
                {players.length > 2 && (
                  <button 
                    onClick={() => removePlayer(player.id)}
                    className="remove-player-btn-compact"
                    title="Remove player"
                  >
                    ✕
                  </button>
                )}
              </div>

              <div className="hole-cards-compact">
                <div className="selected-cards-compact">
                  {player.holeCards.map(card => {
                    const { rank, suit } = formatCard(card);
                    return (
                      <div 
                        key={card} 
                        className={`card-compact ${suit.color}`}
                        onClick={() => selectPlayerCard(player.id, card)}
                        title="Click to remove"
                      >
                        <span className="card-rank">{rank}</span>
                        <span className="card-suit">{suit.symbol}</span>
                      </div>
                    );
                  })}
                  {player.holeCards.length < 2 && (
                    <div className="empty-card-compact">?</div>
                  )}
                  {player.holeCards.length < 2 && (
                    <div className="empty-card-compact">?</div>
                  )}
                </div>
                
                <div className="card-actions-compact">
                  <button 
                    onClick={() => setSelectedPlayer(selectedPlayer === player.id ? null : player.id)}
                    className="select-cards-btn-compact"
                    title={selectedPlayer === player.id ? "Close card picker" : "Select cards"}
                  >
                    {selectedPlayer === player.id ? '✕' : '🃏'}
                  </button>
                  {player.holeCards.length > 0 && (
                    <button 
                      onClick={() => clearPlayerCards(player.id)}
                      className="clear-cards-btn-compact"
                      title="Clear cards"
                    >
                      🗑️
                    </button>
                  )}
                </div>
              </div>

              {/* Card Picker for this player */}
              {selectedPlayer === player.id && (
                <div className="card-picker-overlay" onClick={() => setSelectedPlayer(null)}>
                  <div className="card-picker-modal" onClick={(e) => e.stopPropagation()}>
                    <div className="card-picker-header">
                      <h3>Select Cards for {player.name}</h3>
                      <button 
                        onClick={() => setSelectedPlayer(null)}
                        className="close-picker-btn"
                      >
                        ✕
                      </button>
                    </div>
                    <div className="card-picker-grid">
                      {ranks.map(rank => (
                        <div key={rank} className="card-row">
                          {suits.map(suit => {
                            const card = `${rank}${suit.code}`;
                            const available = isCardAvailable(card);
                            const selected = player.holeCards.includes(card);
                            
                            return (
                              <button
                                key={card}
                                onClick={() => selectPlayerCard(player.id, card)}
                                disabled={!available && !selected}
                                className={`card-button ${suit.color} ${selected ? 'selected' : ''} ${!available ? 'disabled' : ''}`}
                              >
                                <span className="card-rank">{rank}</span>
                                <span className="card-suit">{suit.symbol}</span>
                              </button>
                            );
                          })}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Board Section - More Compact */}
      <div className="board-section-compact">
        <div className="board-header">
          <h2>Board ({boardCards.length}/5)</h2>
          <div className="board-actions">
            <button 
              onClick={() => setSelectingBoard(!selectingBoard)}
              className="select-cards-btn-compact"
              title={selectingBoard ? "Close card picker" : "Select board cards"}
            >
              {selectingBoard ? '✕' : '🃏'}
            </button>
            {boardCards.length > 0 && (
              <button 
                onClick={clearBoard}
                className="clear-cards-btn-compact"
                title="Clear board"
              >
                🗑️
              </button>
            )}
          </div>
        </div>
        
        <div className="selected-cards-compact board-cards-compact">
          {boardCards.map(card => {
            const { rank, suit } = formatCard(card);
            return (
              <div 
                key={card} 
                className={`card-compact ${suit.color}`}
                onClick={() => selectBoardCard(card)}
                title="Click to remove"
              >
                <span className="card-rank">{rank}</span>
                <span className="card-suit">{suit.symbol}</span>
              </div>
            );
          })}
          {[...Array(5 - boardCards.length)].map((_, i) => (
            <div key={i} className="empty-card-compact">?</div>
          ))}
        </div>

        {/* Card Picker for board */}
        {selectingBoard && (
          <div className="card-picker-overlay" onClick={() => setSelectingBoard(false)}>
            <div className="card-picker-modal" onClick={(e) => e.stopPropagation()}>
              <div className="card-picker-header">
                <h3>Select Board Cards</h3>
                <button 
                  onClick={() => setSelectingBoard(false)}
                  className="close-picker-btn"
                >
                  ✕
                </button>
              </div>
              <div className="card-picker-grid">
                {ranks.map(rank => (
                  <div key={rank} className="card-row">
                    {suits.map(suit => {
                      const card = `${rank}${suit.code}`;
                      const available = isCardAvailable(card);
                      const selected = boardCards.includes(card);
                      
                      return (
                        <button
                          key={card}
                          onClick={() => selectBoardCard(card)}
                          disabled={!available && !selected}
                          className={`card-button ${suit.color} ${selected ? 'selected' : ''} ${!available ? 'disabled' : ''}`}
                        >
                          <span className="card-rank">{rank}</span>
                          <span className="card-suit">{suit.symbol}</span>
                        </button>
                      );
                    })}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Settings with Slider - More Compact */}
      <div className="settings-section-compact">
        <div className="iteration-control-compact">
          <div className="iteration-header">
            <label>Iterations: {iterations.toLocaleString()}</label>
            <span className="iteration-time">{getEstimatedTime(iterations)}</span>
          </div>
          
          <input
            type="range"
            min="5000"
            max="50000"
            step="5000"
            value={iterations}
            onChange={(e) => setIterations(parseInt(e.target.value))}
            className="iteration-slider"
          />
          
          <div className="iteration-markers">
            <span onClick={() => setIterations(5000)}>5K</span>
            <span onClick={() => setIterations(10000)}>10K</span>
            <span onClick={() => setIterations(20000)}>20K</span>
            <span onClick={() => setIterations(30000)}>30K</span>
            <span onClick={() => setIterations(40000)}>40K</span>
            <span onClick={() => setIterations(50000)}>50K</span>
          </div>
        </div>
      </div>

      {/* Calculate Button with Tooltip */}
      <div className="calculate-btn-container">
        <button
          onClick={calculateEquity}
          disabled={!isInputValid() || loading}
          className="calculate-btn"
          title={!isInputValid() ? 'All players must have exactly 2 hole cards' : ''}
        >
          {loading ? (
            <span className="loading-content">
              <span className="spinner"></span>
              Calculating...
            </span>
          ) : (
            'Calculate Equity'
          )}
        </button>
      </div>

      {cacheHit && (
        <div className="cache-message">
          ⚡ Results loaded from cache (instant)
        </div>
      )}

      {/* Loading Overlay */}
      {loading && (
        <div className="loading-overlay">
          <div className="loading-card">
            <div className="loading-spinner-large"></div>
            <h3>Calculating Equity</h3>
            <p>Running {iterations.toLocaleString()} simulations...</p>
            <div className="progress-bar">
              <div className="progress-bar-fill"></div>
            </div>
            <p className="loading-tip">💡 Tip: Lower iterations = faster results</p>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="error-message">
          ❌ Error: {error}
        </div>
      )}

      {/* Results Display */}
      {results && (
        <div className="results-section" ref={resultsRef}>
          <h2>Results</h2>
          <p className="results-info">
            Based on {results.iterations.toLocaleString()} simulations
            {results.board_cards && results.board_cards.length > 0 && (
              <span className="results-board-inline">
                {' • Board: '}{results.board_cards.join(', ')}
              </span>
            )}
          </p>

          <div className="results-grid">
            {Object.entries(results.players).map(([name, data]) => {
              const isHighest = name === getHighestEquityPlayer();
              
              return (
                <div 
                  key={name} 
                  className={`result-card ${isHighest ? 'highest-equity' : ''}`}
                >
                  <h3>{name}</h3>
                  
                  <div className="equity-bar-container">
                    <div 
                      className="equity-bar"
                      style={{ width: `${data.equity_percentage}%` }}
                    >
                      <span className="equity-label">
                        {data.equity_percentage.toFixed(2)}%
                      </span>
                    </div>
                  </div>

                  <div className="result-details">
                    <div 
                      className="result-row tooltip-trigger"
                      onMouseEnter={() => handleTooltipEnter('win')}
                      onMouseLeave={handleTooltipLeave}
                    >
                      <span>Win:</span>
                      <span>{data.win_percentage.toFixed(2)}%</span>
                      {showTooltip === 'win' && (
                        <div className="tooltip">
                          <strong>{tooltips.win.title}</strong>
                          <p>{tooltips.win.description}</p>
                        </div>
                      )}
                    </div>
                    <div 
                      className="result-row tooltip-trigger"
                      onMouseEnter={() => handleTooltipEnter('tie')}
                      onMouseLeave={handleTooltipLeave}
                    >
                      <span>Tie:</span>
                      <span>{data.tie_percentage.toFixed(2)}%</span>
                      {showTooltip === 'tie' && (
                        <div className="tooltip">
                          <strong>{tooltips.tie.title}</strong>
                          <p>{tooltips.tie.description}</p>
                        </div>
                      )}
                    </div>
                    <div 
                      className="result-row equity-row tooltip-trigger"
                      onMouseEnter={() => handleTooltipEnter('equity')}
                      onMouseLeave={handleTooltipLeave}
                    >
                      <span>Equity:</span>
                      <span className="equity-value">
                        {data.equity_percentage.toFixed(2)}%
                      </span>
                      {showTooltip === 'equity' && (
                        <div className="tooltip">
                          <strong>{tooltips.equity.title}</strong>
                          <p>{tooltips.equity.description}</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {isHighest && (
                    <div className="highest-badge">🏆 Highest Equity</div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default EquityCalculator;