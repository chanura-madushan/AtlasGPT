import logging
import math
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

EMBEDDING_BATCH_SIZE = 32


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Convert texts into embedding vectors using smaller batches."""

    if not texts:
        return []

    all_embeddings = []
    embedding_dimensions = None
    total_started = time.perf_counter()

    for start in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batch = texts[start:start + EMBEDDING_BATCH_SIZE]
        batch_started = time.perf_counter()

        response = requests.post(
            f"{OLLAMA_URL}/api/embed",
            json={
                "model": EMBEDDING_MODEL,
                "input": batch,
            },
            timeout=120,
        )

        response.raise_for_status()

        try:
            data = response.json()
        except ValueError as exc:
            raise ValueError(
                "Ollama returned an invalid JSON response."
            ) from exc

        if not isinstance(data, dict) or "embeddings" not in data:
            raise ValueError(
                "Ollama response does not contain embeddings."
            )

        embeddings = data["embeddings"]

        if not isinstance(embeddings, list):
            raise ValueError("Ollama returned invalid embeddings.")

        if len(embeddings) != len(batch):
            raise ValueError(
                "Ollama returned an unexpected number of embeddings."
            )

        for embedding in embeddings:
            if (
                not isinstance(embedding, list)
                or not embedding
                or any(
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(value)
                    for value in embedding
                )
            ):
                raise ValueError("Ollama returned an invalid embedding vector.")

            if embedding_dimensions is None:
                embedding_dimensions = len(embedding)
            elif len(embedding) != embedding_dimensions:
                raise ValueError(
                    "Ollama returned embeddings with inconsistent dimensions."
                )

        all_embeddings.extend(embeddings)

        logger.info(
            "Embedding batch: model=%s batch=%d/%d texts=%d elapsed=%.2fs",
            EMBEDDING_MODEL,
            start // EMBEDDING_BATCH_SIZE + 1,
            (len(texts) + EMBEDDING_BATCH_SIZE - 1) // EMBEDDING_BATCH_SIZE,
            len(batch),
            time.perf_counter() - batch_started,
        )

    logger.info(
        "Embedding complete: model=%s texts=%d batches=%d total=%.2fs",
        EMBEDDING_MODEL,
        len(texts),
        (len(texts) + EMBEDDING_BATCH_SIZE - 1) // EMBEDDING_BATCH_SIZE,
        time.perf_counter() - total_started,
    )

    return all_embeddings
