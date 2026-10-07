from src.llm.ollama_client import ask_ollama

answer = ask_ollama("Explain artificial intelligence in one simple sentence.")
print(answer)