import re


DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 100


def split_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """Split text into sentence-aware chunks while preserving paragraphs."""

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size.")

    text = text.strip()

    if not text:
        return []

    paragraphs = re.split(r"\n\s*\n", text)
    chunks = []

    for paragraph in paragraphs:
        sentences = re.split(r"(?<=[.!?])\s+", paragraph.strip())
        current_sentences = []

        for sentence in sentences:
            if len(sentence) > chunk_size:
                if current_sentences:
                    chunks.append(" ".join(current_sentences))
                    current_sentences = []

                words = sentence.split()
                current_words = []
                step = chunk_size - overlap

                for word in words:
                    if len(word) > chunk_size:
                        if current_words:
                            chunks.append(" ".join(current_words))
                            current_words = []

                        for start in range(0, len(word), step):
                            chunks.append(word[start:start + chunk_size])

                        continue

                    candidate = " ".join(current_words + [word])

                    if len(candidate) <= chunk_size:
                        current_words.append(word)
                    else:
                        if current_words:
                            chunks.append(" ".join(current_words))

                        current_words = [word]

                if current_words:
                    chunks.append(" ".join(current_words))

                continue

            candidate = " ".join(current_sentences + [sentence])

            if len(candidate) <= chunk_size:
                current_sentences.append(sentence)
            else:
                if current_sentences:
                    chunks.append(" ".join(current_sentences))

                if overlap > 0 and current_sentences:
                    last_sentence = current_sentences[-1]

                    if len(last_sentence) + 1 + len(sentence) <= chunk_size:
                        current_sentences = [last_sentence, sentence]
                    else:
                        current_sentences = [sentence]
                else:
                    current_sentences = [sentence]

        if current_sentences:
            chunks.append(" ".join(current_sentences))

    return chunks
