"""
FastAPI backend for Poker Learning App

IMPORTANT: This backend contains NO poker strategy assumptions.
All poker ranges are user-defined and loaded from JSON files.

To customize ranges, edit files in: backend/data/ranges/
See backend/data/ranges/README.md for instructions.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router
from range_loader import range_loader

app = FastAPI(
    title="Poker Learning API",
    description="Data-driven poker range viewer. All strategies are user-defined in JSON files.",
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
    print("🃏  Poker Learning API - Starting Up")
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
        "message": "Poker Learning API - Data-Driven Range System",
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
