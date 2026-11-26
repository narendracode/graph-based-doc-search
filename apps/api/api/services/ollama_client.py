from ollama import Client

from api.config import get_settings

settings = get_settings()

_client = Client(host=settings.ollama_host)

# Ollama's own default context window (4096 tokens) is smaller than what a single
# RAG Mode turn can need — system prompt + up to 5 full untruncated 1500-char
# document excerpts + recent chat history routinely exceeds that, and Ollama
# silently truncates whatever doesn't fit rather than erroring, which drops
# grounding context (or the system prompt itself) with no visible symptom besides
# a worse answer. The model's own architectural max is 131072; 8192 comfortably
# covers a real turn (verified: system prompt ~120 tok + 5 chunks ~1900 tok +
# capped history + output) without the far larger KV-cache memory cost of the
# model's full context length.
CHAT_NUM_CTX = 8192


def embed(text: str) -> list[float]:
    response = _client.embeddings(model=settings.ollama_embed_model, prompt=text)
    return response["embedding"]


def embed_many(texts: list[str]) -> list[list[float]]:
    return [embed(t) for t in texts]


def chat(messages: list[dict], stream: bool = False):
    return _client.chat(
        model=settings.ollama_chat_model,
        messages=messages,
        stream=stream,
        options={"num_ctx": CHAT_NUM_CTX},
    )


def generate_json(prompt: str) -> str:
    response = _client.generate(
        model=settings.ollama_chat_model,
        prompt=prompt,
        format="json",
        stream=False,
        options={"num_ctx": CHAT_NUM_CTX},
    )
    return response["response"]
