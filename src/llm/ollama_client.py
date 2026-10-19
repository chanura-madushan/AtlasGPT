import requests
import os

from dotenv import load_dotenv
load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")


def ask_ollama(prompt, history=None):
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": (
    "\n".join(
        f"{message['role']}: {message['content']}"
        for message in (history or [])
    )
    + f"\nuser: {prompt}\nassistant:"
),
                "stream": False
            },
            timeout=120
        )

        response.raise_for_status()
        return response.json()["response"]

    except requests.exceptions.Timeout:
        return "Error: Ollama took too long to respond."

    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to Ollama. Is Ollama running?"

    except requests.exceptions.RequestException as error:
        return f"Error communicating with Ollama: {error}"
