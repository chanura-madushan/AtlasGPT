
from contextlib import asynccontextmanager
from pathlib import Path
import hmac
import os

from dotenv import load_dotenv
from fastapi import (
    Depends,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator

from src.database.conversation_db import init_db
from src.llm.conversation_engine import process_message
from src.rag.ingest import ingest_document
from src.rag.vector_store import list_documents, delete_document


# --------------------------------------------------
# Configuration
# --------------------------------------------------

load_dotenv()

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024

API_KEY = os.getenv("ATLASGPT_API_KEY")

security = HTTPBearer(auto_error=False)


# --------------------------------------------------
# API Key Authentication
# --------------------------------------------------

def require_api_key(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    if not API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key is not configured",
        )

    if credentials is None or not hmac.compare_digest(
        credentials.credentials,
        API_KEY,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )


# --------------------------------------------------
# Database Startup
# --------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="AtlasGPT API",
    description="API for the AtlasGPT AI assistant",
    version="1.0.0",
    lifespan=lifespan,
)


# --------------------------------------------------
# Chat Request Model
# --------------------------------------------------

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


# --------------------------------------------------
# Home Endpoint
# --------------------------------------------------

@app.get("/")
def home():
    return {"message": "AtlasGPT API is running"}


# --------------------------------------------------
# Chat Endpoint
# --------------------------------------------------

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


# --------------------------------------------------
# Upload Document Endpoint
# --------------------------------------------------

@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    _: None = Depends(require_api_key),
):
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided",
        )

    # Handle both Windows and Unix-style paths.
    filename = Path(file.filename.replace("\\", "/")).name
    file_extension = Path(filename).suffix.lower()

    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and TXT files are allowed",
        )

    file_path = UPLOAD_DIR / filename

    # Avoid accidentally replacing an existing document.
    if file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A document with this filename already exists",
        )

    file_content = await file.read(MAX_FILE_SIZE + 1)

    if not file_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty",
        )

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size must not exceed 10 MB",
        )

    try:
        file_path.write_bytes(file_content)

        chunks = ingest_document(str(file_path))

        return {
            "message": "Document uploaded and indexed successfully",
            "filename": filename,
            "chunks": chunks,
        }

    except Exception as error:
        print(f"DOCUMENT PROCESSING ERROR: {error!r}")

        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document upload or processing failed",
        ) from error


# --------------------------------------------------
# List Documents Endpoint
# --------------------------------------------------

@app.get("/documents")
def get_documents(
    _: None = Depends(require_api_key),
):
    return {
        "documents": list_documents(),
    }


# --------------------------------------------------
# Delete Document Endpoint
# --------------------------------------------------

@app.delete("/documents/{filename}")
def remove_document(
    filename: str,
    _: None = Depends(require_api_key),
):
    if Path(filename).name != filename or filename in {".", ".."}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename",
        )

    file_path = UPLOAD_DIR / filename

    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    try:
        delete_document(filename)
        file_path.unlink()

        return {
            "message": "Document deleted successfully",
            "filename": filename,
        }

    except Exception as error:
        print(f"DOCUMENT DELETION ERROR: {error!r}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document deletion failed",
        ) from error
