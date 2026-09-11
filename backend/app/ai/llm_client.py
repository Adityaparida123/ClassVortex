import httpx
from app.config import settings


class LLMClient:
    def __init__(self):
        self.provider = (settings.LLM_PROVIDER or "ollama").lower().strip()
        self.base_url = (settings.OLLAMA_BASE_URL or "").strip().rstrip("/")
        self.model = settings.OLLAMA_MODEL

    @property
    def available(self) -> bool:
        return self.provider == "ollama" and bool(self.base_url) and bool(self.model)

    async def chat(self, messages: list) -> str:
        if not self.available:
            return "AI service is currently unavailable."

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False,
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("message", {}).get("content", "").strip()
                    return content or "I could not generate a response."
                return "AI service is currently unavailable."
        except Exception:
            return "AI service is currently unavailable."


llm_client = LLMClient()