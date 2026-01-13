"""
Ollama Client for Local LLM Integration

Provides a wrapper for Ollama API to enable local, HIPAA-compliant
LLM-based report generation without sending PHI to external services.

SECURITY: All data remains local. No PHI is transmitted externally.
"""

import logging
import requests
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OllamaConfig:
    """Configuration for Ollama client."""
    model: str = "llama3.1:8b"
    base_url: str = "http://localhost:11434"
    temperature: float = 0.3
    max_tokens: int = 2000  # Higher token limit for comprehensive clinical reports
    timeout: int = 300  # seconds (5 minutes for large clinical context)


class OllamaClient:
    """
    Client for interacting with local Ollama LLM.

    Provides a simple interface for generating clinical reports
    using locally-hosted language models.

    HIPAA Compliance:
    - All processing happens locally
    - No data sent to external servers
    - PHI remains on local machine
    """

    def __init__(self, config: Optional[OllamaConfig] = None):
        """
        Initialize Ollama client.

        Args:
            config: Configuration for Ollama connection
        """
        self.config = config or OllamaConfig()
        logger.info(f"Ollama client initialized for model: {self.config.model}")

    def is_available(self) -> bool:
        """
        Check if Ollama service is running and accessible.

        Returns:
            True if Ollama is available, False otherwise
        """
        try:
            response = requests.get(
                f"{self.config.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama not available: {type(e).__name__}")
            return False

    def list_models(self) -> List[str]:
        """
        List available models in Ollama.

        Returns:
            List of model names
        """
        try:
            response = requests.get(
                f"{self.config.base_url}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except Exception as e:
            logger.error(f"Failed to list models: {type(e).__name__}")
            return []

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate text using Ollama.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt for context
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            Generated text

        Raises:
            Exception: If generation fails
        """
        try:
            # Build messages format for chat models
            messages = []
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            messages.append({
                "role": "user",
                "content": prompt
            })

            # Prepare request payload
            payload = {
                "model": self.config.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature or self.config.temperature,
                    "num_predict": max_tokens or self.config.max_tokens
                }
            }

            logger.info(f"Generating response with {self.config.model}")

            # Make request to Ollama
            response = requests.post(
                f"{self.config.base_url}/api/chat",
                json=payload,
                timeout=self.config.timeout
            )

            if response.status_code != 200:
                error_msg = f"Ollama request failed: {response.status_code}"
                logger.error(error_msg)
                raise Exception(error_msg)

            # Extract generated text
            data = response.json()
            generated_text = data.get('message', {}).get('content', '')

            if not generated_text:
                raise Exception("No content generated")

            logger.info(f"Generated {len(generated_text)} characters")
            return generated_text

        except requests.Timeout:
            logger.error("Ollama request timed out")
            raise Exception("Request timed out - model may be too large or system overloaded")
        except Exception as e:
            logger.error(f"Generation failed: {type(e).__name__}")
            raise

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Chat interface for multi-turn conversations.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            Generated response
        """
        try:
            payload = {
                "model": self.config.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature or self.config.temperature,
                    "num_predict": max_tokens or self.config.max_tokens
                }
            }

            response = requests.post(
                f"{self.config.base_url}/api/chat",
                json=payload,
                timeout=self.config.timeout
            )

            if response.status_code != 200:
                raise Exception(f"Request failed: {response.status_code}")

            data = response.json()
            return data.get('message', {}).get('content', '')

        except Exception as e:
            logger.error(f"Chat failed: {type(e).__name__}")
            raise


def create_ollama_client(
    model: str = "llama3.1:8b",
    base_url: str = "http://localhost:11434",
    temperature: float = 0.3
) -> Optional[OllamaClient]:
    """
    Factory function to create Ollama client.

    Args:
        model: Model name to use
        base_url: Ollama API base URL
        temperature: Sampling temperature

    Returns:
        OllamaClient if available, None otherwise
    """
    config = OllamaConfig(
        model=model,
        base_url=base_url,
        temperature=temperature
    )

    client = OllamaClient(config)

    if not client.is_available():
        logger.warning("Ollama service not available")
        return None

    # Check if model is available
    available_models = client.list_models()
    if not available_models:
        logger.warning("No models found in Ollama")
        return None

    if model not in available_models:
        logger.warning(f"Model {model} not found. Available: {available_models}")
        # Try to use first available model
        if available_models:
            logger.info(f"Using {available_models[0]} instead")
            config.model = available_models[0]

    logger.info(f"Ollama client created successfully with model: {config.model}")
    return client


@dataclass
class _Message:
    """Mock OpenAI message structure."""
    content: str


@dataclass
class _Choice:
    """Mock OpenAI choice structure."""
    message: _Message


@dataclass
class _Response:
    """Mock OpenAI response structure."""
    choices: List[_Choice]


class _ChatCompletions:
    """Mock chat.completions structure for OpenAI compatibility."""

    def __init__(self, ollama_client: OllamaClient):
        self.ollama_client = ollama_client

    def create(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ):
        """
        Create chat completion (OpenAI-compatible interface).

        Returns mock response structure.
        """
        # Extract system and user prompts
        system_prompt = None
        user_prompt = None

        for msg in messages:
            if msg['role'] == 'system':
                system_prompt = msg['content']
            elif msg['role'] == 'user':
                user_prompt = msg['content']

        # Generate response
        content = self.ollama_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )

        # Return proper OpenAI-compatible response structure
        return _Response(
            choices=[_Choice(message=_Message(content=content))]
        )


class _Chat:
    """Mock chat structure with completions attribute."""

    def __init__(self, ollama_client: OllamaClient):
        self.completions = _ChatCompletions(ollama_client)


class OllamaLLMAdapter:
    """
    Adapter to make OllamaClient compatible with ReportGenerator.

    Provides OpenAI-style interface for compatibility.
    """

    def __init__(self, ollama_client: OllamaClient):
        """Initialize adapter with Ollama client."""
        self.ollama_client = ollama_client
        # Create mock structure for compatibility (OpenAI-style: client.chat.completions.create)
        self.chat = _Chat(ollama_client)
