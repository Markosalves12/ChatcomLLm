import requests
from django.conf import settings

TIMEOUT = 120


def _url(path: str) -> str:
    return f"{settings.LMSTUDIO_URL.rstrip('/')}/{path.lstrip('/')}"


def chat(mensagens: list[dict], temperature: float = 0.2) -> str:
    r = requests.post(
        _url("/chat/completions"),

        headers={
            "Authorization": f"Bearer {settings.LMSTUDIO_API_KEY}",
            "Content-Type": "application/json",
        },

        json={
            "model": settings.LMSTUDIO_CHAT_MODEL,
            "messages": mensagens,
            "temperature": temperature,
        },

        timeout=TIMEOUT,
    )

    r.raise_for_status()

    return r.json()["choices"][0]["message"]["content"]