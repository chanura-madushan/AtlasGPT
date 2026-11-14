import pytest

from src.rag.chunker import split_text


def test_empty_text_returns_empty_list():
    assert split_text("") == []
    assert split_text("   ") == []


def test_short_text_returns_one_chunk():
    text = "Python is a programming language."

    chunks = split_text(text)

    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunks_do_not_exceed_chunk_size():
    text = "A" * 1200

    chunks = split_text(text, chunk_size=500, overlap=50)

    assert all(len(chunk) <= 500 for chunk in chunks)


def test_chunks_have_expected_overlap():
    text = "A" * 1200

    chunks = split_text(text, chunk_size=500, overlap=50)

    assert chunks[0][-50:] == chunks[1][:50]
    assert chunks[1][-50:] == chunks[2][:50]


def test_invalid_chunk_size_raises_error():
    with pytest.raises(ValueError):
        split_text("Some text", chunk_size=0)


def test_invalid_overlap_raises_error():
    with pytest.raises(ValueError):
        split_text("Some text", chunk_size=100, overlap=100)


def test_chunks_prefer_sentence_boundaries():
    text = (
        "Python is easy to learn. "
        "It is widely used for machine learning. "
        "Developers also use it for automation."
    )

    chunks = split_text(text, chunk_size=55, overlap=0)

    assert chunks[0].endswith(".")


def test_sentence_chunks_preserve_overlap():
    text = (
        "Alpha sentence. "
        "Bravo sentence. "
        "Charlie sentence."
    )

    chunks = split_text(text, chunk_size=40, overlap=5)

    assert len(chunks) > 1
    assert "Bravo sentence." in chunks[0]
    assert chunks[1].startswith("Bravo sentence.")


def test_chunks_preserve_paragraph_boundaries():
    text = (
        "Python is a programming language.\n\n"
        "It is used for automation and data science."
    )

    chunks = split_text(text, chunk_size=100, overlap=0)

    assert len(chunks) == 2
    assert chunks[0] == "Python is a programming language."
    assert chunks[1] == "It is used for automation and data science."


def test_sentence_overlap_does_not_exceed_chunk_size():
    text = (
        "Alpha sentence. "
        "Bravo sentence. "
        "Charlie sentence. "
        "Delta sentence."
    )

    chunks = split_text(text, chunk_size=40, overlap=10)

    assert all(len(chunk) <= 40 for chunk in chunks)


def test_long_sentence_chunks_respect_size_limit():
    text = " ".join(["machinelearning"] * 100)

    chunks = split_text(text, chunk_size=100, overlap=10)

    assert len(chunks) > 1
    assert all(len(chunk) <= 100 for chunk in chunks)


def test_long_sentence_does_not_split_words():
    text = " ".join(["machinelearning"] * 100)

    chunks = split_text(text, chunk_size=100, overlap=10)

    for chunk in chunks:
        assert all(word == "machinelearning" for word in chunk.split())