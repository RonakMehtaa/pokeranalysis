# Ollama LLM Integration Guide

## Overview

The Poker Learning Tool integrates with **Ollama** to provide AI-powered hand analysis and explanations.

**IMPORTANT:** The LLM integration does NOT generate poker strategy. It only provides educational explanations based on user-defined range data from JSON files.

## What is Ollama?

Ollama is a local LLM runtime that runs models like Llama, Mistral, and others on your machine. It provides:
- **Privacy**: All data stays on your computer
- **No API costs**: Free to use
- **Fast responses**: Local inference
- **Multiple models**: Choose the best model for your needs

Official site: https://ollama.ai/

## Installation

### macOS

```bash
# Download and install from https://ollama.ai/download
# Or use Homebrew:
brew install ollama
```

### Linux

```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Windows

Download the installer from https://ollama.ai/download

## Setup

### 1. Start Ollama Service

```bash
ollama serve
```

The service will start on `http://localhost:11434`

### 2. Pull a Model

Download a model (one-time setup):

```bash
# Recommended: Llama 3.2 (fast, accurate)
ollama pull llama3.2

# Alternative: Mistral (compact, good performance)
ollama pull mistral

# Alternative: Llama 3.1 (larger, more capable)
ollama pull llama3.1
```

### 3. Verify Installation

```bash
# List installed models
ollama list

# Test the model
ollama run llama3.2 "Hello, how are you?"
```

### 4. Configure Backend

Create `.env` file in `backend/` directory:

```bash
cp .env.example .env
```

Edit `.env` to set your model:

```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
OLLAMA_TIMEOUT=30
```

## Usage

### Check LLM Health

```bash
curl http://localhost:8000/api/llm/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "base_url": "http://localhost:11434",
  "configured_model": "llama3.2",
  "available_models": ["llama3.2", "mistral"],
  "model_available": true
}
```

### Analyze a Hand

```bash
curl -X POST http://localhost:8000/api/llm/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "hand": "AKs",
    "position": "BTN",
    "table_type": "6max",
    "action": "open",
    "context": "Tight passive table with deep stacks"
  }'
```

The LLM will provide an educational explanation based on:
1. User-defined range data from JSON files
2. The hand's characteristics
3. The context you provide

## How It Works

### Data Flow

1. **User Request** → Frontend sends hand + context
2. **Range Lookup** → Backend loads user-defined action from JSON
3. **Prompt Construction** → Backend builds educational prompt with range data
4. **LLM Analysis** → Ollama generates explanation
5. **Response** → Combined range data + LLM analysis returned

### What the LLM Receives

```
Hand: AKs
Position: BTN
Table Type: 6max
Action Context: open

Range Data (User-Defined):
- Recommended Action: raise
- Range Explanation: Premium suited broadway. Excellent hand from button.

Additional Context: Tight passive table with deep stacks

Please provide:
1. A clear explanation of why this hand is played this way
2. Key factors that make this hand raise
3. Common mistakes players make
4. How this hand performs postflop
```

The LLM does NOT decide the action — it only explains the user-defined action.

## Model Recommendations

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| **llama3.2** | ~2GB | Fast | Good | Default choice |
| **mistral** | ~4GB | Fast | Good | Alternative |
| **llama3.1** | ~4.7GB | Medium | Better | Detailed analysis |
| **llama3.1:70b** | ~40GB | Slow | Best | Advanced users |

Start with `llama3.2` — it's fast and works well for poker explanations.

## Troubleshooting

### "Cannot connect to Ollama"

**Solution:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it:
ollama serve
```

### "Model not found"

**Solution:**
```bash
# Pull the model
ollama pull llama3.2

# Verify it's installed
ollama list
```

### "Request timed out"

**Causes:**
- Model too large for your hardware
- First request (model loading into memory)
- Heavy system load

**Solutions:**
1. Increase timeout in `.env`: `OLLAMA_TIMEOUT=60`
2. Use a smaller model: `OLLAMA_MODEL=mistral`
3. Wait for first request (model loads into RAM)

### "Model available: false"

**Solution:**
```bash
# Your .env has a model that's not installed
# Either pull it:
ollama pull llama3.2

# Or change .env to use an installed model:
OLLAMA_MODEL=mistral
```

## Performance Tips

### Speed Up Responses

1. **Keep Ollama running**: Don't stop `ollama serve`
2. **Use smaller models**: `llama3.2` > `llama3.1` > `llama3.1:70b`
3. **Warm up the model**: First request loads model into RAM (slow), subsequent requests are fast
4. **Adequate RAM**: 8GB minimum, 16GB recommended

### Improve Quality

1. **Use larger models**: `llama3.1` or `llama3.1:70b` for detailed analysis
2. **Provide context**: Add specific table dynamics in the `context` field
3. **Edit prompts**: Modify prompt in `routes.py` for your teaching style

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | `llama3.2` | Model name to use |
| `OLLAMA_TIMEOUT` | `30` | Request timeout (seconds) |

## Security & Privacy

✅ **All data stays local** - No external API calls  
✅ **No telemetry** - Ollama doesn't send data anywhere  
✅ **No API keys** - Free to use  
✅ **Offline capable** - Works without internet after model download  

## Architecture Notes

The LLM integration is designed to be:
- **Strategy-agnostic**: No poker logic in the LLM client
- **Data-driven**: All strategy from JSON files
- **Fail-safe**: Graceful error handling if Ollama is down
- **Configurable**: Easy to swap models or adjust settings

The backend NEVER asks the LLM to generate poker strategy. It only asks the LLM to explain user-defined decisions in educational terms.

## API Integration Points

| Endpoint | Purpose | LLM Used? |
|----------|---------|-----------|
| `GET /api/ranges` | List ranges | ❌ No |
| `GET /api/range` | Get range matrix | ❌ No |
| `POST /api/decision/preflop` | Get action | ❌ No |
| `GET /api/llm/health` | Check Ollama | ✅ Yes (health check) |
| `POST /api/llm/analyze` | Analyze hand | ✅ Yes (analysis) |

Only the `/llm/*` endpoints use Ollama. Core functionality works without it.

---

**Need Help?** Check the [API Documentation](API_DOCUMENTATION.md) for request/response examples.
