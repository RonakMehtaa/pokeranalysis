import React from 'react'

function Home() {
  return (
    <div className="page home-page">
      <div className="hero">
        <h1>Learn Preflop Poker Strategy</h1>
        <p className="subtitle">
          Master live 1-2 poker preflop decisions with interactive ranges and instant feedback
        </p>
      </div>

      <div className="features">
        <div className="feature-card">
          <h2>📊 Range Viewer</h2>
          <p>
            Explore preflop opening, calling, and 3-betting ranges for 6-max and 9-max tables.
            Visual charts with explanations for every hand.
          </p>
          <a href="/ranges" className="btn">View Ranges</a>
        </div>

        <div className="feature-card">
          <h2>🎯 Decision Checker</h2>
          <p>
            Input your hand and situation, get instant GTO-inspired advice.
            Understand the "why" behind every decision.
          </p>
          <a href="/checker" className="btn">Check Decision</a>
        </div>
      </div>

      <div className="info-section">
        <h3>Built for Learning</h3>
        <p>
          This tool focuses on building intuition and muscle memory for preflop play.
          Perfect for study sessions and post-game review.
        </p>
      </div>
    </div>
  )
}

export default Home
