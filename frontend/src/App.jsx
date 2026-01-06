import React from 'react'
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import Home from './pages/Home'
import RangeViewer from './pages/RangeViewer'
import DecisionChecker from './pages/DecisionChecker'
import PostflopAnalysis from './pages/PostflopAnalysis'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <nav className="navbar">
          <div className="nav-container">
            <h1 className="logo">Poker Learning Tool</h1>
            <div className="nav-links">
              <Link to="/">Home</Link>
              <Link to="/ranges">Range Viewer</Link>
              <Link to="/checker">Decision Checker</Link>
              <Link to="/postflop">Postflop Analysis</Link>
            </div>
          </div>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/ranges" element={<RangeViewer />} />
            <Route path="/checker" element={<DecisionChecker />} />
            <Route path="/postflop" element={<PostflopAnalysis />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
