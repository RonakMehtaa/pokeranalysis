# Poker Analysis Tool API Documentation

## Base URL
```
http://localhost:8000/api
```

## Core Endpoints

### 1. Get Available Ranges
```http
GET /api/ranges
```

Returns metadata about loaded range files.

**Response:**
```json
{
  "table_types": ["6max", "9max"],
  "positions": {
    "6max": ["UTG", "MP", "CO", "BTN", "SB", "BB"],
    "9max": ["UTG", "UTG+1", "MP", "MP+1", "CO", "BTN", "SB", "BB"]
  },
  "actions": ["open", "call", "3bet"],
  "loaded_ranges": [...],
  "total_ranges": 1
}
```

---

### 2. Get Specific Range
```http
GET /api/range?table_type=6max&position=BTN&action=open
```

Returns full 13×13 hand matrix (169 hands) from user-defined JSON file.

**Query Parameters:**
- `table_type` (required): `6max` or `9max`
- `position` (required): `UTG`, `MP`, `CO`, `BTN`, `SB`, `BB`
- `action` (required): `open`, `call`, or `3bet`

**Response:**
```json
{
  "table_type": "6max",
  "position": "BTN",
  "action": "open",
  "hands": {
    "AA": "raise",
    "KK": "raise",
    "72o": "fold",
    ...
  },
  "explanations": {
    "AA": "Premium pocket pair. Always raise from the button.",
    ...
  }
}
```

---

### 3. Get Preflop Decision
```http
POST /api/decision/preflop
```

Get recommended action for a specific hand from user-defined ranges.

**Request Body:**
```json
{
  "table_type": "6max",
  "position": "BTN",
  "hero_hand": "AKs",
  "prior_action": "folded"
}
```

**Response:**
```json
{
  "recommended_action": "raise",
  "explanation": "Premium suited broadway. Excellent hand from button.",
  "hand": "AKs",
  "table_type": "6max",
  "position": "BTN",
  "prior_action": "folded"
}
```

---

## LLM Endpoints (Ollama Integration)

### 4. Check LLM Health
```http
GET /api/llm/health
```

Check if Ollama is running and accessible.

**Response (Healthy):**
```json
{
  "status": "healthy",
  "base_url": "http://localhost:11434",
  "configured_model": "llama3.2",
  "available_models": ["llama3.2", "llama3.1", "mistral"],
  "model_available": true
}
```

**Response (Unhealthy):**
```json
{
  "status": "unhealthy",
  "base_url": "http://localhost:11434",
  "configured_model": "llama3.2",
  "error": "Cannot connect to Ollama..."
}
```

---

### 5. Analyze Hand with LLM
```http
POST /api/llm/analyze
```

Get detailed LLM analysis of a hand based on user-defined range data.

**IMPORTANT:** This endpoint does NOT generate poker strategy. It sends user-defined range data to the LLM for educational explanation.

**Request Body:**
```json
{
  "hand": "AKs",
  "position": "BTN",
  "table_type": "6max",
  "action": "open",
  "context": "Tight table, deep stacks"
}
```

**Response:**
```json
{
  "hand": "AKs",
  "position": "BTN",
  "table_type": "6max",
  "action": "open",
  "recommended_action": "raise",
  "range_explanation": "Premium suited broadway...",
  "llm_analysis": "This hand is a strong raise because...",
  "source": "user_defined_range + llm_analysis"
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid hand format: AK. Use format like AKs, 77, QJo"
}
```

### 503 Service Unavailable
```json
{
  "detail": "LLM service error: Cannot connect to Ollama at http://localhost:11434..."
}
```

---

## Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
OLLAMA_TIMEOUT=30
```

See `.env.example` for all options.

---

## Testing with cURL

### Test range endpoint:
```bash
curl "http://localhost:8000/api/range?table_type=6max&position=BTN&action=open"
```

### Test decision endpoint:
```bash
curl -X POST http://localhost:8000/api/decision/preflop \
  -H "Content-Type: application/json" \
  -d '{
    "table_type": "6max",
    "position": "BTN",
    "hero_hand": "AKs",
    "prior_action": "folded"
  }'
```

### Test LLM health:
```bash
curl http://localhost:8000/api/llm/health
```

### Test LLM analysis:
```bash
curl -X POST http://localhost:8000/api/llm/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "hand": "AKs",
    "position": "BTN",
    "table_type": "6max",
    "action": "open",
    "context": "Tight passive table"
  }'
```

---

## Notes

- All poker strategy comes from JSON files in `backend/data/ranges/`
- The backend contains NO hardcoded poker logic
- LLM responses are based on user-defined range data
- Missing ranges default to all-fold with helpful messages
