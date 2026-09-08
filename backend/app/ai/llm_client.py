import httpx
from app.config import settings


class LLMClient:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL

    async def chat(self, messages: list) -> str:
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
                    return data.get("message", {}).get("content", "I could not generate a response.")
                return "AI service is currently unavailable."
        except Exception:
            return "AI service is currently unavailable."


llm_client = LLMClient()
