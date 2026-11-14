from pathlib import Path

from src.rag.chunker import split_text
from src.rag.embeddings import embed_texts
from src.rag.retriever import retrieve_context
from src.rag.vector_store import add_documents, delete_document


USER_ID = 99991

FIXTURE_DIR = Path("tests/fixtures/retrieval")

QUESTIONS = {
    "python.txt": {
        "question": "Which libraries are used to build machine learning models in Python?",
        "expected_text": "Scikit-learn",
    },
    "machine_learning.txt": {
        "question": "How do computers discover patterns and learn from examples?",
        "expected_text": "Supervised learning",
    },
    "database.txt": {
        "question": "What technology organizes information and allows SQL queries?",
        "expected_text": "relational databases",
    },
    "data_science.txt": {
        "question": "Which field uses statistics and programming to extract insights from data?",
        "expected_text": "interdisciplinary field",
    },
}

def index_documents():
    for filename in QUESTIONS.keys():
        file_path = FIXTURE_DIR / filename
        text = file_path.read_text(encoding="utf-8")

        chunks = split_text(text)
        embeddings = embed_texts(chunks)

        add_documents(
            chunks=chunks,
            embeddings=embeddings,
            source=filename,
            user_id=USER_ID,
        )

        print(f"Indexed: {filename} ({len(chunks)} chunks)")

def check_retrieval():
    passed = 0
    total = len(QUESTIONS)

    for filename, test_case in QUESTIONS.items():
        question = test_case["question"]
        expected_text = test_case["expected_text"]

        results = retrieve_context(
            question=question,
            user_id=USER_ID,
            n_results=3,
        )

        print(f"\nQuestion: {question}")

        if not results:
            print("FAIL: No relevant results found.")
            continue

        top_result = results[0]

        if top_result["source"] != filename:
            print(f"FAIL: Expected {filename}, got {top_result['source']}")
            continue

        if expected_text.lower() not in top_result["text"].lower():
            print("FAIL: Correct document, but expected answer text was not found.")
            continue

        passed += 1
        print("PASS: Correct document and chunk retrieved.")

        for result in results:
            print(
                f"Source: {result['source']} | "
                f"Distance: {result['distance']:.4f}"
            )

    accuracy = passed / total * 100
    print(f"\nRetrieval accuracy: {passed}/{total} ({accuracy:.1f}%)")


def cleanup():
    for filename in QUESTIONS:
        delete_document(
            source=filename,
            user_id=USER_ID,
        )


if __name__ == "__main__":
    try:
        index_documents()
        check_retrieval()
    finally:
        cleanup()
        print("\nTest documents cleaned up.")