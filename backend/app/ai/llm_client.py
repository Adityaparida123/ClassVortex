import logging
import httpx
from app.config import settings

logger = logging.getLogger("attendvortex.ai")

AI_UNAVAILABLE_MESSAGE = "AI service is currently unavailable."
AI_TIMEOUT_MESSAGE = "AI request timed out. Please try again."
USER_FRIENDLY_UNAVAILABLE = "The AI service is currently unavailable. Please try again later."
USER_FRIENDLY_AVAILABLE = "LLM service is reachable"


def _new_async_client(timeout: float) -> httpx.AsyncClient:
    """Testable seam around httpx.AsyncClient construction."""
    return httpx.AsyncClient(timeout=timeout)


class LLMClient:
    def __init__(self):
        self.provider = (settings.LLM_PROVIDER or "ollama").lower().strip()
        self.base_url = (settings.OLLAMA_BASE_URL or "").strip().rstrip("/")
        self.model = settings.OLLAMA_MODEL
        self.ollama_api_key = (settings.OLLAMA_API_KEY or "").strip()
        self.openai_base_url = (settings.OPENAI_COMPATIBLE_BASE_URL or "").strip().rstrip("/")
        self.openai_model = settings.OPENAI_COMPATIBLE_MODEL
        self.openai_api_key = (settings.OPENAI_COMPATIBLE_API_KEY or "").strip()

    def _config_reason(self):
        """Return why the model backend cannot be used, or None if configured."""
        if self.provider == "ollama":
            if not self.base_url:
                return "OLLAMA_BASE_URL is not configured."
            if not self.model:
                return "OLLAMA_MODEL is not configured."
            return None
        if self.provider == "openai_compatible":
            if not self.openai_base_url:
                return "OPENAI_COMPATIBLE_BASE_URL is not configured."
            if not self.openai_model:
                return "OPENAI_COMPATIBLE_MODEL is not configured."
            return None
        return f"LLM_PROVIDER '{self.provider}' is not supported. Use 'ollama' or 'openai_compatible'."

    @property
    def available(self) -> bool:
        return self._config_reason() is None

    @property
    def display_model(self) -> str:
        return self.openai_model if self.provider == "openai_compatible" else self.model

    def _ollama_headers(self) -> dict:
        if self.ollama_api_key:
            return {"Authorization": f"Bearer {self.ollama_api_key}"}
        return {}

    async def health(self) -> dict:
        """Lightweight connectivity check.

        Never crashes when the LLM is down and never exposes URLs, keys, or
        secrets. The `message` field is always user-friendly; the `reason`
        field carries technical detail and is server-side only.
        """
        reason = self._config_reason()
        if reason:
            return {
                "available": False,
                "provider": self.provider,
                "model": self.display_model,
                "message": USER_FRIENDLY_UNAVAILABLE,
                "reason": reason,
            }
        try:
            async with _new_async_client(timeout=5.0) as client:
                if self.provider == "ollama":
                    resp = await client.get(
                        f"{self.base_url}/api/tags", headers=self._ollama_headers()
                    )
                else:
                    headers = {}
                    if self.openai_api_key:
                        headers["Authorization"] = f"Bearer {self.openai_api_key}"
                    resp = await client.get(f"{self.openai_base_url}/models", headers=headers)

                if resp.status_code != 200:
                    logger.warning(
                        "LLM health check (provider=%s) failed with HTTP %s",
                        self.provider,
                        resp.status_code,
                    )
                    return {
                        "available": False,
                        "provider": self.provider,
                        "model": self.display_model,
                        "message": USER_FRIENDLY_UNAVAILABLE,
                        "reason": f"{self.provider} endpoint returned HTTP {resp.status_code}.",
                    }

                # Ollama exposes the installed model tags; OpenAI-compatible
                # servers expose their model list. Report a model mismatch but
                # still consider the connection reachable.
                if self.provider == "ollama":
                    models = [m.get("name", "") for m in (resp.json().get("models") or [])]
                    if models and not any(
                        self.model == name or self.model in name or name.startswith(self.model)
                        for name in models
                    ):
                        logger.warning(
                            "LLM health check (provider=%s): model '%s' not found in installed models",
                            self.provider,
                            self.model,
                        )
                        return {
                            "available": False,
                            "provider": self.provider,
                            "model": self.display_model,
                            "message": USER_FRIENDLY_UNAVAILABLE,
                            "reason": f"Configured model '{self.model}' was not found on the Ollama server.",
                        }

                return {
                    "available": True,
                    "provider": self.provider,
                    "model": self.display_model,
                    "message": USER_FRIENDLY_AVAILABLE,
                    "reason": None,
                }
        except httpx.TimeoutException:
            logger.warning("LLM health check (provider=%s) timed out", self.provider)
            return {
                "available": False,
                "provider": self.provider,
                "model": self.display_model,
                "message": USER_FRIENDLY_UNAVAILABLE,
                "reason": "Timed out while connecting to the LLM service.",
            }
        except Exception as e:
            technical = f"Could not reach the LLM service: {e.__class__.__name__}."
            logger.warning("LLM health check failed (provider=%s): %s", self.provider, technical)
            return {
                "available": False,
                "provider": self.provider,
                "model": self.display_model,
                "message": USER_FRIENDLY_UNAVAILABLE,
                "reason": technical,
            }

    async def chat(self, messages: list) -> str:
        reason = self._config_reason()
        if reason:
            logger.warning("LLM chat skipped (provider=%s): %s", self.provider, reason)
            return AI_UNAVAILABLE_MESSAGE

        try:
            timeout = settings.LLM_TIMEOUT_SECONDS
            async with _new_async_client(timeout=timeout) as client:
                if self.provider == "ollama":
                    response = await client.post(
                        f"{self.base_url}/api/chat",
                        json={
                            "model": self.model,
                            "messages": messages,
                            "stream": False,
                        },
                        headers=self._ollama_headers(),
                    )
                    if response.status_code == 200:
                        data = response.json()
                        content = data.get("message", {}).get("content", "").strip()
                        return content or AI_UNAVAILABLE_MESSAGE
                    return AI_UNAVAILABLE_MESSAGE

                headers = {}
                if self.openai_api_key:
                    headers["Authorization"] = f"Bearer {self.openai_api_key}"
                response = await client.post(
                    f"{self.openai_base_url}/chat/completions",
                    json={
                        "model": self.openai_model,
                        "messages": messages,
                        "stream": False,
                    },
                    headers=headers,
                )
                if response.status_code == 200:
                    data = response.json()
                    choices = data.get("choices") or []
                    content = ""
                    if choices:
                        content = (choices[0].get("message", {}).get("content", "") or "").strip()
                    return content or AI_UNAVAILABLE_MESSAGE
                return AI_UNAVAILABLE_MESSAGE
        except httpx.TimeoutException:
            logger.warning("LLM chat timed out (provider=%s)", self.provider)
            return AI_TIMEOUT_MESSAGE
        except Exception as e:
            logger.warning(
                "LLM chat failed (provider=%s): %s", self.provider, e.__class__.__name__
            )
            return AI_UNAVAILABLE_MESSAGE


llm_client = LLMClient()