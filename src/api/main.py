
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from src.llm.ollama_client import ask_ollama

app = FastAPI()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message cannot be blank or whitespace only")
        return value


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
