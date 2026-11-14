
import os
import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")



def embed_texts(texts: list[str]) -> list[list[float]]:
    #Convert a list of texts into embedding vectors.

    if not texts:
        return []

    response = requests.post(
        f"{OLLAMA_URL}/api/embed",
        json={
            "model": EMBEDDING_MODEL,
            "input": texts,
        },
        timeout=120,
    )

    response.raise_for_status()

    try:
        data = response.json()
    except ValueError as exc:
        raise ValueError("Ollama returned an invalid JSON response.") from exc

    if not isinstance(data, dict) or "embeddings" not in data:
        raise ValueError("Ollama response does not contain embeddings.")

    embeddings = data["embeddings"]

    if not isinstance(embeddings, list):
        raise ValueError("Ollama returned invalid embeddings.")

    if len(embeddings) != len(texts):
        raise ValueError("Ollama returned an unexpected number of embeddings.")

    return embeddings
