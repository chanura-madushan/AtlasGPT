from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.llm.ollama_client import ask_ollama

app = FastAPI()


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def home():
    return {"message": "AtlasGPT API is running"}


@app.post("/chat")
def chat(request: ChatRequest):
    answer = ask_ollama(request.message)

    if answer.startswith("Error:"):
        raise HTTPException(
            status_code=503,
            detail=answer
        )

    return {"reply": answer}