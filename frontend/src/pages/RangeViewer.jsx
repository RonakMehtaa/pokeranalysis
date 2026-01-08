import React, { useState, useEffect } from 'react'

function RangeViewer() {
  const [tableType, setTableType] = useState('6max')
  const [position, setPosition] = useState('BTN')
  const [action, setAction] = useState('open')
  const [rangeData, setRangeData] = useState(null)
  const [selectedHand, setSelectedHand] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const positions6max = ['UTG', 'MP', 'CO', 'BTN', 'SB', 'BB']
  const positions9max = ['UTG', 'UTG+1', 'MP', 'MP+1', 'HJ', 'CO', 'BTN', 'SB', 'BB']
  const positions = tableType === '6max' ? positions6max : positions9max

  // Generate the 13x13 hand matrix layout
  const generateHandMatrix = () => {
    const ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
    const matrix = []

    for (let row = 0; row < 13; row++) {
      const rowHands = []
      for (let col = 0; col < 13; col++) {
        let hand
        if (row === col) {
          // Pairs on diagonal
          hand = ranks[row] + ranks[col]
        } else if (col > row) {
          // Suited hands above diagonal
          hand = ranks[row] + ranks[col] + 's'
        } else {
          // Offsuit hands below diagonal
          hand = ranks[col] + ranks[row] + 'o'
        }
        rowHands.push(hand)
      }
      matrix.push(rowHands)
    }
    return matrix
  }

  const handMatrix = generateHandMatrix()

  // Fetch range data from API
  useEffect(() => {
    const fetchRange = async () => {
      setLoading(true)
      setError(null)
      try {
        // Properly encode URL parameters to handle + characters in positions like UTG+1 and MP+1
        const params = new URLSearchParams({
          table_type: tableType,
          position: position,
          action: action
        })
        
        const response = await fetch(
          `http://localhost:8000/api/range?${params.toString()}`
        )
        
        if (!response.ok) {
          throw new Error('Range not available for this configuration')
        }
        
        const data = await response.json()
        setRangeData(data)
      } catch (err) {
        setError(err.message)
        setRangeData(null)
      } finally {
        setLoading(false)
      }
    }

    fetchRange()
  }, [tableType, position, action])

  // Get color for a hand based on action
  const getHandColor = (hand) => {
    if (!rangeData || !rangeData.hands) return 'fold'
    const handAction = rangeData.hands[hand]
    return handAction || 'fold'
  }

  // Get CSS class for hand action
  const getHandClass = (hand) => {
    const action = getHandColor(hand)
    return `hand-cell ${action}`
  }

  // Handle hand click
  const handleHandClick = (hand) => {
    if (!rangeData) return
    
    const handAction = rangeData.hands[hand] || 'fold'
    const explanation = rangeData.explanations[hand] || getDefaultExplanation(hand, handAction)
    
    setSelectedHand({
      hand,
      action: handAction,
      explanation
    })
  }

  const getDefaultExplanation = (hand, action) => {
    if (action === 'raise') {
      return 'This hand is in your opening range from this position.'
    } else if (action === 'fold') {
      return 'This hand is too weak to play from this position.'
    } else if (action === 'call') {
      return 'This hand is best played with a call in this spot.'
    } else if (action === '3bet') {
      return 'This hand should be 3-bet for value or as a bluff.'
    }
    return 'No explanation available.'
  }

  return (
    <div className="page range-viewer-page">
      <h1>Preflop Range Viewer</h1>
      <p className="subtitle">Explore GTO-inspired opening ranges with explanations</p>
      
      <div className="controls">
        {/* Table Type */}
        <div className="control-group">
          <label>Table Type</label>
          <div className="button-group">
            <button 
              className={tableType === '6max' ? 'active' : ''}
              onClick={() => {
                setTableType('6max')
                setPosition('BTN')
              }}
            >
              6-Max
            </button>
            <button 
              className={tableType === '9max' ? 'active' : ''}
              onClick={() => {
                setTableType('9max')
                setPosition('BTN')
              }}
            >
              9-Max
            </button>
          </div>
        </div>

        {/* Position */}
        <div className="control-group">
          <label>Position</label>
          <div className="button-group position-group">
            {positions.map(pos => (
              <button 
                key={pos}
                className={position === pos ? 'active' : ''}
                onClick={() => setPosition(pos)}
              >
                {pos}
              </button>
            ))}
          </div>
        </div>

        {/* Action Type */}
        <div className="control-group">
          <label>Action</label>
          <div className="button-group">
            <button 
              className={action === 'open' ? 'active' : ''}
              onClick={() => setAction('open')}
            >
              Open
            </button>
            <button 
              className={action === 'call' ? 'active' : ''}
              onClick={() => setAction('call')}
            >
              Call
            </button>
            <button 
              className={action === '3bet' ? 'active' : ''}
              onClick={() => setAction('3bet')}
            >
              3-Bet
            </button>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="legend">
        <div className="legend-item">
          <span className="legend-color raise"></span>
          <span>Raise</span>
        </div>
        <div className="legend-item">
          <span className="legend-color call"></span>
          <span>Call</span>
        </div>
        <div className="legend-item">
          <span className="legend-color 3bet"></span>
          <span>3-Bet</span>
        </div>
        <div className="legend-item">
          <span className="legend-color fold"></span>
          <span>Fold</span>
        </div>
      </div>

      {loading && (
        <div className="loading">Loading range data...</div>
      )}

      {error && (
        <div className="error-message">
          ⚠️ {error}
          <p className="error-hint">This range configuration is not available yet.</p>
        </div>
      )}

      {rangeData && !loading && (
        <div className="range-container">
          {/* Hand Matrix */}
          <div className="hand-matrix">
            {handMatrix.map((row, rowIndex) => (
              <div key={rowIndex} className="matrix-row">
                {row.map((hand, colIndex) => (
                  <div
                    key={`${rowIndex}-${colIndex}`}
                    className={getHandClass(hand)}
                    onClick={() => handleHandClick(hand)}
                    title={hand}
                  >
                    {hand}
                  </div>
                ))}
              </div>
            ))}
          </div>

          {/* Selected Hand Info */}
          {selectedHand && (
            <div className="hand-info">
              <div className="hand-info-header">
                <h3>{selectedHand.hand}</h3>
                <span className={`action-badge ${selectedHand.action}`}>
                  {selectedHand.action.toUpperCase()}
                </span>
              </div>
              <p className="hand-explanation">{selectedHand.explanation}</p>
              <button 
                className="close-btn"
                onClick={() => setSelectedHand(null)}
              >
                Close
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default RangeViewer
