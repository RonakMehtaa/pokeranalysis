"""
FastAPI backend for Poker Analysis App

IMPORTANT: This backend contains NO hardcoded poker strategy.
All poker decisions are loaded from user-defined JSON files in backend/data/ranges/

This is a pure data delivery layer with optional AI analysis features.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router
from range_loader import range_loader

app = FastAPI(
    title="Poker Analysis API",
    description="Data-driven poker analysis tool. All strategies are user-defined in JSON files.",
    version="1.0.0"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:3005"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")

@app.on_event("startup")
def startup_event():
    """
    Load all user-defined preflop ranges from JSON files on server startup.
    
    Poker ranges are user-defined and can be edited manually.
    No strategy is hardcoded in this backend.
    """
    print("=" * 60)
    print("🃏  Poker Analysis API - Starting Up")
    print("=" * 60)
    print()
    print("📂 Loading user-defined ranges from JSON files...")
    print("   (Poker ranges are user-defined and can be edited manually)")
    print()
    
    range_loader.load_all_ranges()
    
    print()
    print("✅ Server ready!")
    print("=" * 60)
    print()

@app.get("/")
def read_root():
    return {
        "message": "Poker Analysis API - Data-Driven Range System",
        "status": "active",
        "version": "1.0.0",
        "note": "All poker ranges are user-defined and loaded from JSON files. No strategy is hardcoded."
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "ranges_loaded": len(range_loader.ranges)
    }
