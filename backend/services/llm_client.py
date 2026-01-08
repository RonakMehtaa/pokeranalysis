"""
LLM Client Service - Ollama Integration

IMPORTANT: This service does NOT contain poker strategy logic.
It only handles communication with the Ollama API.

All poker strategy prompts are constructed by the caller.
This is purely a wrapper for LLM API calls.
"""

import httpx
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration from environment variables
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))

print(f"🔧 Ollama Configuration:")
print(f"   Base URL: {OLLAMA_BASE_URL}")
print(f"   Model: {OLLAMA_MODEL}")
print(f"   Timeout: {OLLAMA_TIMEOUT}s")


class OllamaClient:
    """
    Client for communicating with Ollama API.
    
    This class does NOT generate poker strategy.
    It only sends prompts to Ollama and returns responses.
    """
    
    def __init__(
        self, 
        base_url: str = OLLAMA_BASE_URL,
        model: str = OLLAMA_MODEL,
        timeout: int = OLLAMA_TIMEOUT
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.generate_url = f"{self.base_url}/api/generate"
        
    async def analyze_hand(self, prompt: str) -> str:
        """
        Send a prompt to Ollama and return the response.
        
        This method does NOT create poker strategy.
        The caller must construct the full prompt with all context.
        
        Args:
            prompt: The complete prompt to send to the LLM
            
        Returns:
            The LLM's text response
            
        Raises:
            Exception: If Ollama is unreachable or times out
        """
        try:
            print(f"📤 Sending request to Ollama at {self.generate_url}")
            print(f"   Model: {self.model}, Timeout: {self.timeout}s")
            
            # Log the full prompt being sent
            print("\n" + "="*80)
            print("📝 FULL PROMPT BEING SENT TO OLLAMA:")
            print("="*80)
            print(prompt)
            print("="*80 + "\n")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.generate_url,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "top_p": 0.9,
                        }
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                print(f"✅ Received response from Ollama")
                return result.get("response", "").strip()
                
        except httpx.TimeoutException:
            error_msg = (
                f"Ollama request timed out after {self.timeout} seconds. "
                f"This usually means:\n"
                f"1. Ollama is loading the model into RAM (first request is slow)\n"
                f"2. The model is too large for your system\n"
                f"3. Ollama is not running\n\n"
                f"Solutions:\n"
                f"- Wait and try again (first request can take 60-120 seconds)\n"
                f"- Increase OLLAMA_TIMEOUT in .env file\n"
                f"- Use a smaller model: ollama pull llama3.2\n"
                f"- Check if Ollama is running: curl {self.base_url}/api/tags"
            )
            print(f"❌ Timeout error: {error_msg}")
            raise Exception(error_msg)
            
        except httpx.ConnectError:
            error_msg = (
                f"Cannot connect to Ollama at {self.base_url}. "
                f"Ollama is not running or not reachable.\n\n"
                f"Solutions:\n"
                f"1. Start Ollama: ollama serve\n"
                f"2. Check if running: curl {self.base_url}/api/tags\n"
                f"3. Install Ollama: https://ollama.ai/download\n"
                f"4. Pull a model: ollama pull llama3.2"
            )
            print(f"❌ Connection error: {error_msg}")
            raise Exception(error_msg)
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                error_msg = (
                    f"Model '{self.model}' not found in Ollama.\n\n"
                    f"Solutions:\n"
                    f"1. Pull the model: ollama pull {self.model}\n"
                    f"2. Check installed models: ollama list\n"
                    f"3. Update OLLAMA_MODEL in .env to match an installed model"
                )
            else:
                error_msg = f"Ollama API error: {e.response.status_code} - {e.response.text}"
            
            print(f"❌ HTTP error: {error_msg}")
            raise Exception(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error calling Ollama: {str(e)}"
            print(f"❌ Unexpected error: {error_msg}")
            raise Exception(error_msg)
    
    async def check_health(self) -> dict:
        """
        Check if Ollama is running and accessible.
        
        Returns:
            Dictionary with status information
        """
        try:
            print(f"🔍 Checking Ollama health at {self.base_url}")
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                
                models = response.json().get("models", [])
                model_names = [m.get("name") for m in models]
                
                print(f"✅ Ollama is healthy. Models: {model_names}")
                
                return {
                    "status": "healthy",
                    "base_url": self.base_url,
                    "configured_model": self.model,
                    "available_models": model_names,
                    "model_available": self.model in model_names
                }
        except Exception as e:
            print(f"❌ Ollama health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "base_url": self.base_url,
                "configured_model": self.model,
                "error": str(e)
            }


# Global instance - configured from environment variables
# No poker strategy is stored here
ollama_client = OllamaClient()
