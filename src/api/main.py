
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from src.llm.ollama_client import ask_ollama
from src.database.conversation_db import (
    get_history,
    init_db,
    save_message,
)

app = FastAPI()
@app.on_event("startup")
def startup():
    init_db()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: str = Field(min_length=1, max_length=100)
    user_id: int = Field(gt=0)

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
    history = get_history(
        request.user_id,
        conversation_id=request.conversation_id,
    )

    answer = ask_ollama(request.message, history=history)

    if answer.startswith("Error:"):
        raise HTTPException(
            status_code=503,
            detail=answer,
        )

    save_message(
        request.user_id,
        "user",
        request.message,
        conversation_id=request.conversation_id,
    )

    save_message(
        request.user_id,
        "assistant",
        answer,
        conversation_id=request.conversation_id,
    )

    return {"reply": answer}

