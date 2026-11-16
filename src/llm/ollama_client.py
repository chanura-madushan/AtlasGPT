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
                "stream": False,
            },
            timeout=120,
        )

        response.raise_for_status()

        data = response.json()
        answer = data.get("response") if isinstance(data, dict) else None

        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("Invalid Ollama response format")

        return answer

    except requests.exceptions.Timeout:
        return "Error: Ollama took too long to respond."

    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to Ollama. Is Ollama running?"

    except requests.exceptions.RequestException:
        return "Error: Could not communicate with Ollama."

    except (ValueError, TypeError):
        return "Error: Ollama returned an invalid response."
