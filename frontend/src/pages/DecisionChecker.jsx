import React, { useState } from 'react'

function DecisionChecker() {
  const [tableType, setTableType] = useState('6max')
  const [position, setPosition] = useState('BTN')
  const [heroHand, setHeroHand] = useState('')
  const [priorAction, setPriorAction] = useState('folded')
  const [raiseSize, setRaiseSize] = useState('3bb')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const positions6max = ['UTG', 'MP', 'CO', 'BTN', 'SB', 'BB']
  const positions9max = ['UTG', 'UTG+1', 'MP', 'MP+1', 'CO', 'BTN', 'SB', 'BB']
  const positions = tableType === '6max' ? positions6max : positions9max

  const ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
  const [selectedRank1, setSelectedRank1] = useState('')
  const [selectedRank2, setSelectedRank2] = useState('')
  const [suited, setSuited] = useState(false)

  // Generate hand notation from card selector
  const generateHandNotation = () => {
    if (!selectedRank1 || !selectedRank2) return ''
    
    // Sort ranks by strength (A highest)
    const rank1Index = ranks.indexOf(selectedRank1)
    const rank2Index = ranks.indexOf(selectedRank2)
    
    let hand = ''
    if (rank1Index === rank2Index) {
      // Pair
      hand = selectedRank1 + selectedRank2
    } else if (rank1Index < rank2Index) {
      // First rank is higher
      hand = selectedRank1 + selectedRank2 + (suited ? 's' : 'o')
    } else {
      // Second rank is higher
      hand = selectedRank2 + selectedRank1 + (suited ? 's' : 'o')
    }
    
    return hand
  }

  // Update hand notation when selections change
  React.useEffect(() => {
    const hand = generateHandNotation()
    setHeroHand(hand)
  }, [selectedRank1, selectedRank2, suited])

  const handleGetRecommendation = async () => {
    if (!heroHand) {
      setError('Please select your hand')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch('http://localhost:8000/api/decision/preflop', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          table_type: tableType,
          position: position,
          hero_hand: heroHand,
          prior_action: priorAction,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to get recommendation')
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const clearSelection = () => {
    setSelectedRank1('')
    setSelectedRank2('')
    setSuited(false)
    setHeroHand('')
    setResult(null)
  }

  return (
    <div className="page decision-checker-page">
      <h1>Decision Checker</h1>
      <p className="subtitle">Get instant preflop recommendations for any situation</p>

      <div className="checker-form">
        {/* Table Type */}
        <div className="form-section">
          <label>Table Type</label>
          <div className="button-group">
            <button 
              className={tableType === '6max' ? 'active' : ''}
              onClick={() => {
                setTableType('6max')
                if (!positions6max.includes(position)) {
                  setPosition('BTN')
                }
              }}
            >
              6-Max
            </button>
            <button 
              className={tableType === '9max' ? 'active' : ''}
              onClick={() => {
                setTableType('9max')
                if (!positions9max.includes(position)) {
                  setPosition('BTN')
                }
              }}
            >
              9-Max
            </button>
          </div>
        </div>

        {/* Position */}
        <div className="form-section">
          <label>Your Position</label>
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

        {/* Action Before You */}
        <div className="form-section">
          <label>Action Before You</label>
          <div className="button-group">
            <button 
              className={priorAction === 'folded' ? 'active' : ''}
              onClick={() => setPriorAction('folded')}
            >
              Folded to You
            </button>
            <button 
              className={priorAction === 'limpers' ? 'active' : ''}
              onClick={() => setPriorAction('limpers')}
            >
              Limpers
            </button>
            <button 
              className={priorAction === 'raise' ? 'active' : ''}
              onClick={() => setPriorAction('raise')}
            >
              Facing Raise
            </button>
          </div>
        </div>

        {priorAction === 'raise' && (
          <div className="form-section">
            <label>Raise Size</label>
            <input 
              type="text"
              value={raiseSize}
              onChange={(e) => setRaiseSize(e.target.value)}
              placeholder="e.g., 3bb, 5bb"
            />
          </div>
        )}

        {/* Card Selector */}
        <div className="form-section">
          <label>Your Hand</label>
          <div className="card-selector">
            <div className="rank-selector">
              <label className="small-label">First Card</label>
              <div className="rank-grid">
                {ranks.map(rank => (
                  <button
                    key={rank}
                    className={`rank-btn ${selectedRank1 === rank ? 'selected' : ''}`}
                    onClick={() => setSelectedRank1(rank)}
                  >
                    {rank}
                  </button>
                ))}
              </div>
            </div>

            <div className="rank-selector">
              <label className="small-label">Second Card</label>
              <div className="rank-grid">
                {ranks.map(rank => (
                  <button
                    key={rank}
                    className={`rank-btn ${selectedRank2 === rank ? 'selected' : ''}`}
                    onClick={() => setSelectedRank2(rank)}
                  >
                    {rank}
                  </button>
                ))}
              </div>
            </div>

            {selectedRank1 && selectedRank2 && selectedRank1 !== selectedRank2 && (
              <div className="suited-selector">
                <label className="small-label">Suited?</label>
                <div className="button-group">
                  <button
                    className={!suited ? 'active' : ''}
                    onClick={() => setSuited(false)}
                  >
                    Offsuit
                  </button>
                  <button
                    className={suited ? 'active' : ''}
                    onClick={() => setSuited(true)}
                  >
                    Suited
                  </button>
                </div>
              </div>
            )}

            {heroHand && (
              <div className="hand-display">
                <span className="hand-label">Your Hand:</span>
                <span className="hand-value">{heroHand}</span>
                <button className="clear-hand-btn" onClick={clearSelection}>×</button>
              </div>
            )}
          </div>
        </div>

        {error && (
          <div className="error-message">
            ⚠️ {error}
          </div>
        )}

        <button 
          className="btn-primary" 
          onClick={handleGetRecommendation}
          disabled={!heroHand || loading}
        >
          {loading ? 'Analyzing...' : 'Get Recommendation'}
        </button>
      </div>

      {/* Result Display */}
      {result && (
        <div className="result-area result-filled">
          <div className="result-header">
            <div className="result-hand">
              <span className="hand-badge">{result.hand}</span>
              <span className="position-badge">{result.position} • {result.table_type}</span>
            </div>
            <div className={`result-action ${result.recommended_action}`}>
              {result.recommended_action.toUpperCase()}
            </div>
          </div>
          
          <div className="result-explanation">
            <p>{result.explanation}</p>
          </div>

          {result.prior_action !== 'folded' && (
            <div className="result-note">
              <strong>Note:</strong> Currently showing opening ranges only. 
              Full calling and 3-bet ranges coming soon!
            </div>
          )}
        </div>
      )}

      {!result && !error && !loading && (
        <div className="result-area">
          <p className="placeholder-text">
            Select your hand and situation above to get a recommendation
          </p>
        </div>
      )}
    </div>
  )
}

export default DecisionChecker
