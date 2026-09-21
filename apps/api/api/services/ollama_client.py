from ollama import Client

from api.config import get_settings

settings = get_settings()

_client = Client(host=settings.ollama_host)


def embed(text: str) -> list[float]:
    response = _client.embeddings(model=settings.ollama_embed_model, prompt=text)
    return response["embedding"]


def embed_many(texts: list[str]) -> list[list[float]]:
    return [embed(t) for t in texts]


def chat(messages: list[dict], stream: bool = False):
    return _client.chat(model=settings.ollama_chat_model, messages=messages, stream=stream)


def generate_json(prompt: str) -> str:
    response = _client.generate(
        model=settings.ollama_chat_model, prompt=prompt, format="json", stream=False
    )
    return response["response"]
