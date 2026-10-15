from fastapi import FastAPI
from pydantic import BaseModel
from src.llm.ollama_client import ask_ollama

class ChatRequest(BaseModel):
    message: str

app = FastAPI()

@app.get("/")
def home():
    return {"message": "AtlasGPT API is running"}


@app.post("/chat")
def chat(request: ChatRequest):
    answer = ask_ollama(request.message)
    return {"reply": answer}