# Poker Learning Tool

**A data-driven educational web app for mastering preflop poker decisions.**

## 🎯 Purpose

This tool helps poker players learn and memorize preflop ranges through:
- Interactive range charts with explanations
- Instant decision recommendations
- **AI-powered hand analysis** (optional Ollama integration)
- Clean, distraction-free UI optimized for learning

## ⚠️ Important: Data-Driven Architecture

**This backend contains NO poker strategy assumptions.**

All poker ranges are user-defined and loaded from JSON files only. You have complete control over the strategy being taught.

**Poker ranges are user-defined and can be edited manually** in:
```
backend/data/ranges/
```

See `backend/data/ranges/README.md` for detailed instructions on editing ranges.

## 🧱 Tech Stack

**Frontend:** React (JavaScript) + Vite  
**Backend:** Python + FastAPI  
**Data:** JSON files (no database needed)  
**LLM (Optional):** Ollama (local AI for hand analysis)

## 📁 Project Structure

```
LearnPoker/
├── backend/
│   ├── main.py              # FastAPI app (NO strategy logic)
│   ├── routes.py            # API endpoints (pure data delivery)
│   ├── range_loader.py      # JSON file loader (NO strategy)
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example         # Environment config template
│   ├── OLLAMA_SETUP.md      # LLM integration guide
│   ├── API_DOCUMENTATION.md # Complete API reference
│   ├── services/
│   │   └── llm_client.py    # Ollama API client (NO strategy)
│   └── data/
│       └── ranges/          # USER-DEFINED POKER RANGES (JSON)
│           ├── README.md    # How to edit ranges
│           └── 6max_BTN_open.json  # SAMPLE DATA ONLY
└── frontend/
    ├── src/
    │   ├── pages/           # Route components
    │   ├── App.jsx          # Main app with routing
    │   └── main.jsx         # Entry point
    ├── index.html
    ├── package.json
    └── vite.config.js
```

## 🃏 Range Files (User-Defined)

### Sample Data Included

The file `backend/data/ranges/6max_BTN_open.json` contains **SAMPLE PLACEHOLDER DATA** for demonstration purposes only. This is NOT GTO strategy - it's just example data showing the format.

### Full 13×13 Matrix Required

Each range file must define all **169 poker hands**:
- Pairs (13): AA, KK, QQ, ..., 22
- Suited (78): AKs, AQs, ..., 32s
- Offsuit (78): AKo, AQo, ..., 32o

**Missing hands automatically default to "fold"** with an explanation.

### How to Add Your Own Ranges

1. Copy the sample file as a template:
   ```bash
   cp backend/data/ranges/6max_BTN_open.json backend/data/ranges/6max_UTG_open.json
   ```

2. Edit the JSON file to define your strategy

3. Restart the backend server to load the new range

See `backend/data/ranges/README.md` for complete documentation.

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+** 
- **Node.js 16+** and npm
- **Ollama** (optional, for LLM features) - see [Ollama Setup Guide](backend/OLLAMA_SETUP.md)

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. **(Optional) Configure Ollama:**
```bash
# Copy environment template
cp .env.example .env

# Install Ollama from https://ollama.ai
# Pull a model
ollama pull llama3.2

# Start Ollama service
ollama serve
```

See `backend/OLLAMA_SETUP.md` for complete LLM integration guide.

5. Start the server:
```bash
uvicorn main:app --reload --port 8000
```

The backend will be running at: **http://localhost:8000**

API documentation: **http://localhost:8000/docs**

### Frontend Setup

1. Open a new terminal and navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the dev server:
```bash
npm run dev
```

The frontend will be running at: **http://localhost:5173**

## 🧪 Testing the Setup

1. Backend health check:
```bash
curl http://localhost:8000/health
```

2. Check loaded ranges:
```bash
curl http://localhost:8000/api/ranges
```

3. Get a specific range:
```bash
curl "http://localhost:8000/api/range?table_type=6max&position=BTN&action=open"
```

4. **(Optional) Check LLM integration:**
```bash
curl http://localhost:8000/api/llm/health
```

5. Open browser to http://localhost:5173

## 📚 Features

✅ **Range Viewer**
- Visual 13×13 hand matrix
- Color-coded by action (raise/call/fold/3-bet)
- Click any hand for detailed explanation
- Select table type, position, and action

✅ **Decision Checker**
- Input your specific hand
- Get recommended action
- See detailed explanation
- Based on your custom ranges

✅ **AI-Powered Analysis (Optional)**
- Deep hand analysis using local LLM (Ollama)
- Educational explanations of user-defined strategy
- Context-aware recommendations
- **100% privacy** - runs locally on your machine

✅ **Clean UI**
- Poker-friendly dark green theme
- Professional study tool aesthetic
- Mobile responsive
- Easy to read for long study sessions

✅ **Data-Driven Backend**
- NO hardcoded poker strategy
- Load ranges from JSON files
- Full 169-hand matrix support
- Automatic fold defaults for missing hands
- Optional LLM integration (works without it)

## 🤖 LLM Integration (Optional)

The app includes **optional** integration with Ollama for AI-powered hand analysis.

### Key Points:
- ✅ **Completely optional** - core features work without it
- ✅ **Privacy-first** - runs 100% locally on your machine
- ✅ **No API costs** - free to use with any Ollama model
- ✅ **Strategy-agnostic** - LLM explains your user-defined ranges, doesn't create strategy

### Setup:
```bash
# Install Ollama
brew install ollama  # macOS

# Pull a model
ollama pull llama3.2

# Start Ollama
ollama serve

# Configure backend
cp backend/.env.example backend/.env
# Edit .env to set OLLAMA_MODEL=llama3.2
```

See **[backend/OLLAMA_SETUP.md](backend/OLLAMA_SETUP.md)** for complete setup guide.

### API Endpoints:
- `GET /api/llm/health` - Check if Ollama is running
- `POST /api/llm/analyze` - Get AI analysis of a hand

See **[backend/API_DOCUMENTATION.md](backend/API_DOCUMENTATION.md)** for API reference.

## 🎨 Customization

### Adding New Ranges

1. Create a JSON file following the naming convention:
   ```
   {table_type}_{position}_{action}.json
   ```

2. Examples:
   - `6max_UTG_open.json` - UTG opening range
   - `6max_CO_3bet.json` - CO 3-bet range
   - `9max_MP_open.json` - Middle position opening for 9-max

3. Required JSON structure:
   ```json
   {
     "table_type": "6max",
     "position": "UTG",
     "action": "open",
     "hands": {
       "AA": "raise",
       "KK": "raise",
       "72o": "fold",
       ...
     },
     "explanations": {
       "AA": "Premium pocket pair...",
       ...
     }
   }
   ```

4. Restart the backend to load new ranges

### Valid Values

- **Table types:** `6max`, `9max`
- **Positions (6-max):** `UTG`, `MP`, `CO`, `BTN`, `SB`, `BB`
- **Positions (9-max):** `UTG`, `UTG+1`, `MP`, `MP+1`, `CO`, `BTN`, `SB`, `BB`
- **Actions:** `open`, `call`, `3bet`
- **Hand actions:** `raise`, `call`, `fold`, `3bet`

## 🛠️ Development Commands

### Backend
```bash
# Run with auto-reload
uvicorn main:app --reload --port 8000

# Run in production mode
uvicorn main:app --host 0.0.0.0 --port 8000

# Optional: Start Ollama for LLM features
ollama serve
```

### Frontend
```bash
# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## 📝 Architecture Notes

- **No TypeScript** - pure JavaScript for simplicity
- **No database** - ranges stored as JSON files
- **No authentication** - educational tool, not a web service
- **Data-driven** - zero poker strategy in backend code
- **User-customizable** - edit JSON files to change strategy
- **Fail-safe** - missing ranges default to all-fold
- **Optional LLM** - AI features are entirely optional

## 🔒 What the Backend Does NOT Do

- ❌ Generate poker ranges algorithmically
- ❌ Calculate GTO solutions
- ❌ Make strategy assumptions
- ❌ Hardcode any poker advice
- ❌ Send data to external APIs (when using Ollama)

The backend is purely a **data delivery layer** that loads user-defined JSON files.

The optional LLM integration only explains user-defined strategy - it never generates new strategy.

## 🎓 Educational Philosophy

This tool prioritizes **learning and memorization** over solver-perfect GTO. Users define their own ranges based on their preferred strategy, opponents, and game conditions.

The optional AI assistant helps explain your ranges in educational terms, but never overrides your strategy decisions.

## 📖 Documentation

- **[API_DOCUMENTATION.md](backend/API_DOCUMENTATION.md)** - Complete API reference with examples
- **[OLLAMA_SETUP.md](backend/OLLAMA_SETUP.md)** - LLM integration setup guide
- **[data/ranges/README.md](backend/data/ranges/README.md)** - How to create custom ranges

---

**Status:** ✅ Fully functional data-driven range system with optional AI analysis

**To customize:** Edit JSON files in `backend/data/ranges/`  
**For AI features:** See `backend/OLLAMA_SETUP.md`
