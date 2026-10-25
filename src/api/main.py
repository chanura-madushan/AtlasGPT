
import os
import secrets
from contextlib import asynccontextmanager
from src.llm.conversation_engine import process_message
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator

from src.database.conversation_db import (
    get_history,
    init_db,
    save_message,
)
from src.llm.ollama_client import ask_ollama

load_dotenv()

API_KEY = os.getenv("ATLASGPT_API_KEY", "").strip()
bearer_scheme = HTTPBearer(auto_error=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)


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

    @field_validator("conversation_id")
    @classmethod
    def conversation_id_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Conversation ID cannot be blank")
        return value


def require_api_key(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> None:
    if not API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication is not configured",
        )

    if credentials is None or not secrets.compare_digest(
        credentials.credentials, API_KEY
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.get("/")
def home():
    return {"message": "AtlasGPT API is running"}



@app.post("/chat")
def chat(
    request: ChatRequest,
    _: None = Depends(require_api_key),
):
    answer = process_message(
        user_id=request.user_id,
        conversation_id=request.conversation_id,
        message=request.message,
    )

    if answer.startswith("Error:"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The language model service is temporarily unavailable",
        )

    return {"reply": answer}
