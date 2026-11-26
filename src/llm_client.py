"""
ArchSynth LLM Client - Unified wrapper for Gemini API and Ollama local models.

Provides structured output with Pydantic schema validation, retries, and fallback.
"""

import os
import json
import time
import logging
from typing import Type, TypeVar, Optional, Any, Dict, List
from abc import ABC, abstractmethod

from pydantic import BaseModel, ValidationError
try:
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
except ImportError:
    def retry(*args, **kwargs):
        def decorator(f):
            return f
        return decorator
    def stop_after_attempt(*args, **kwargs): return None
    def wait_exponential(*args, **kwargs): return None
    def retry_if_exception_type(*args, **kwargs): return None

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    from pathlib import Path as _EnvPath
    _env_file = _EnvPath(".env")
    if _env_file.exists():
        for _line in _env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class LLMError(Exception):
    """Base exception for LLM errors"""
    pass


class SchemaValidationError(LLMError):
    """Raised when LLM output fails schema validation"""
    pass


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 8192
    ) -> T:
        """Generate structured output matching the given schema"""
        pass

    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 8192
    ) -> str:
        """Generate free-form text output"""
        pass


class GeminiProvider(LLMProvider):
    """Google Gemini API provider"""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise LLMError("GEMINI_API_KEY not set in environment or .env file")

        self.model_name = model

        # Import and configure Gemini
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(model)
            self.genai = genai
        except ImportError:
            raise LLMError("google-generativeai not installed. Run: pip install google-generativeai")

    def _create_schema_instruction(self, schema: Type[BaseModel]) -> str:
        """Create instruction for structured JSON output"""
        schema_dict = schema.model_json_schema()
        return f"""
You MUST output valid JSON that matches this exact schema:
```json
{json.dumps(schema_dict, indent=2)}
```

Rules:
1. Output ONLY the JSON object, no markdown, no explanation
2. All required fields must be present
3. Use proper JSON types (strings, numbers, arrays, objects)
4. For enums, use the exact string values from the schema
5. If a field is optional and you don't have info, use null or omit it
"""

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((SchemaValidationError, json.JSONDecodeError))
    )
    def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 8192
    ) -> T:
        """Generate structured output with schema validation"""

        full_prompt = f"{prompt}\n\n{self._create_schema_instruction(schema)}"

        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{full_prompt}"

        try:
            response = self.client.generate_content(
                full_prompt,
                generation_config=self.genai.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    response_mime_type="application/json"
                )
            )

            if not response.text:
                raise SchemaValidationError("Empty response from Gemini")

            # Parse and validate
            data = json.loads(response.text)
            return schema.model_validate(data)

        except json.JSONDecodeError as e:
            logger.warning(f"Gemini returned invalid JSON: {e}. Response: {response.text[:500]}")
            raise SchemaValidationError(f"Invalid JSON from LLM: {e}")
        except ValidationError as e:
            logger.warning(f"Schema validation failed: {e}")
            raise SchemaValidationError(f"Output doesn't match schema: {e}")

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 8192
    ) -> str:
        """Generate free-form text"""
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{full_prompt}"

        response = self.client.generate_content(
            full_prompt,
            generation_config=self.genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
        )

        return response.text or ""


class OllamaProvider(LLMProvider):
    """Local Ollama provider for open-weight models"""

    def __init__(self, host: str = "http://localhost:11434", model: str = "qwen2.5-coder"):
        self.host = host
        self.model = model

        try:
            import ollama
            self.client = ollama.Client(host=host)
            # Verify model exists
            models_response = self.client.list()
            model_list = getattr(models_response, 'models', None)
            if model_list is None and isinstance(models_response, dict):
                model_list = models_response.get('models', [])
            model_list = model_list or []

            model_names = []
            for m in model_list:
                name = getattr(m, 'model', None) or getattr(m, 'name', None)
                if not name and isinstance(m, dict):
                    name = m.get('model') or m.get('name')
                if name:
                    model_names.append(str(name))

            if model not in model_names and f"{model}:latest" not in model_names:
                logger.warning(f"Model '{model}' not found in Ollama. Available: {model_names}")
        except ImportError:
            raise LLMError("ollama not installed. Run: pip install ollama")
        except Exception as e:
            raise LLMError(f"Failed to connect to Ollama at {host}: {e}")

    @staticmethod
    def _extract_content(response: Any) -> str:
        """Extract text content from Ollama ChatResponse or dict"""
        if hasattr(response, 'message') and hasattr(response.message, 'content'):
            return response.message.content or ""
        if isinstance(response, dict):
            return response.get('message', {}).get('content', '') or ""
        if hasattr(response, 'get'):
            msg = response.get('message', {})
            if isinstance(msg, dict):
                return msg.get('content', '') or ""
            elif hasattr(msg, 'content'):
                return getattr(msg, 'content', '') or ""
        return str(response)

    def _create_schema_instruction(self, schema: Type[BaseModel]) -> str:
        """Create instruction for structured JSON output"""
        schema_dict = schema.model_json_schema()
        return f"""
You MUST output valid JSON that matches this exact schema:
```json
{json.dumps(schema_dict, indent=2)}
```

Rules:
1. Output ONLY the JSON object, no markdown, no explanation
2. All required fields must be present
3. Use proper JSON types (strings, numbers, arrays, objects)
4. For enums, use the exact string values from the schema
5. If a field is optional and you don't have info, use null or omit it
"""

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((SchemaValidationError, json.JSONDecodeError))
    )
    def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 8192
    ) -> T:
        """Generate structured output with schema validation"""

        full_prompt = f"{prompt}\n\n{self._create_schema_instruction(schema)}"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": full_prompt})

        try:
            chat_kwargs: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            try:
                response = self.client.chat(**chat_kwargs, format="json")
            except TypeError:
                chat_kwargs["options"]["format"] = "json"
                response = self.client.chat(**chat_kwargs)

            content = self._extract_content(response)
            if not content:
                raise SchemaValidationError("Empty response from Ollama")

            data = json.loads(content)
            return schema.model_validate(data)

        except json.JSONDecodeError as e:
            logger.warning(f"Ollama returned invalid JSON: {e}. Content: {content[:500] if 'content' in locals() else 'None'}")
            raise SchemaValidationError(f"Invalid JSON from LLM: {e}")
        except ValidationError as e:
            logger.warning(f"Schema validation failed: {e}")
            raise SchemaValidationError(f"Output doesn't match schema: {e}")

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 8192
    ) -> str:
        """Generate free-form text"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat(
            model=self.model,
            messages=messages,
            options={
                "temperature": temperature,
                "num_predict": max_tokens
            }
        )

        return self._extract_content(response)


class LLMClient:
    """
    Unified LLM client with automatic fallback and provider selection.

    Usage:
        client = LLMClient(primary="gemini", fallback="ollama")
        result = client.generate_structured(prompt, MySchema)
    """

    def __init__(
        self,
        primary: str = "gemini",
        fallback: Optional[str] = "ollama",
        gemini_model: str = "gemini-2.5-flash",
        ollama_model: str = "qwen2.5-coder",
        ollama_host: str = "http://localhost:11434"
    ):
        self.primary_name = primary
        self.fallback_name = fallback
        self.providers: Dict[str, LLMProvider] = {}

        # Initialize primary provider
        if primary == "gemini":
            try:
                self.providers["gemini"] = GeminiProvider(model=gemini_model)
            except Exception as e:
                logger.warning(f"Could not initialize Gemini provider: {e}")
        elif primary == "ollama":
            try:
                self.providers["ollama"] = OllamaProvider(host=ollama_host, model=ollama_model)
            except Exception as e:
                logger.warning(f"Could not initialize Ollama provider: {e}")
        else:
            raise ValueError(f"Unknown primary provider: {primary}")

        # Initialize fallback provider
        if fallback and fallback != primary:
            if fallback == "gemini":
                try:
                    self.providers["gemini"] = GeminiProvider(model=gemini_model)
                except Exception as e:
                    logger.warning(f"Could not initialize fallback Gemini provider: {e}")
            elif fallback == "ollama":
                try:
                    self.providers["ollama"] = OllamaProvider(host=ollama_host, model=ollama_model)
                except Exception as e:
                    logger.warning(f"Could not initialize fallback Ollama provider: {e}")

        logger.info(f"LLMClient initialized: primary={primary}, fallback={fallback}")

    def get_provider(self, name: str) -> LLMProvider:
        """Get provider by name"""
        if name not in self.providers:
            raise ValueError(f"Provider '{name}' not initialized. Available: {list(self.providers.keys())}")
        return self.providers[name]

    def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 8192,
        provider: Optional[str] = None
    ) -> T:
        """
        Generate structured output with automatic fallback.

        Args:
            prompt: User prompt
            schema: Pydantic model class for validation
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Max output tokens
            provider: Specific provider to use (overrides primary/fallback)

        Returns:
            Validated Pydantic model instance
        """
        providers_to_try = []

        if provider:
            providers_to_try = [provider]
        else:
            providers_to_try = [self.primary_name]
            if self.fallback_name and self.fallback_name != self.primary_name:
                providers_to_try.append(self.fallback_name)

        last_error = None
        for provider_name in providers_to_try:
            try:
                provider_obj = self.get_provider(provider_name)
                logger.info(f"Calling {provider_name} for structured generation...")
                return provider_obj.generate_structured(
                    prompt, schema, system_prompt, temperature, max_tokens
                )
            except Exception as e:
                last_error = e
                logger.warning(f"Provider {provider_name} failed: {e}")
                if provider_name == providers_to_try[-1]:
                    break  # Last provider, will raise

        raise LLMError(f"All providers failed. Last error: {last_error}")

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 8192,
        provider: Optional[str] = None
    ) -> str:
        """Generate free-form text with fallback"""
        providers_to_try = []

        if provider:
            providers_to_try = [provider]
        else:
            providers_to_try = [self.primary_name]
            if self.fallback_name and self.fallback_name != self.primary_name:
                providers_to_try.append(self.fallback_name)

        last_error = None
        for provider_name in providers_to_try:
            try:
                provider_obj = self.get_provider(provider_name)
                return provider_obj.generate_text(prompt, system_prompt, temperature, max_tokens)
            except Exception as e:
                last_error = e
                logger.warning(f"Provider {provider_name} failed: {e}")
                if provider_name == providers_to_try[-1]:
                    break

        raise LLMError(f"All providers failed. Last error: {last_error}")


# Convenience function for quick usage
_default_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create default LLM client"""
    global _default_client
    if _default_client is None:
        _default_client = LLMClient(
            primary=os.getenv("PRIMARY_LLM", "gemini"),
            fallback=os.getenv("FALLBACK_LLM", "ollama"),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            ollama_model=os.getenv("OLLAMA_MODEL", "qwen2.5-coder"),
            ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434")
        )
    return _default_client


def call_llm_structured(prompt: str, schema: Type[T], **kwargs) -> T:
    """Convenience function for structured LLM calls"""
    return get_llm_client().generate_structured(prompt, schema, **kwargs)


def call_llm_text(prompt: str, **kwargs) -> str:
    """Convenience function for text LLM calls"""
    return get_llm_client().generate_text(prompt, **kwargs)