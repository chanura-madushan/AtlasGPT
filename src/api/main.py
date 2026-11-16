import logging
import time
from collections import defaultdict, deque
from threading import Lock
from contextlib import asynccontextmanager
from pathlib import Path
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
from src.llm.conversation_engine import process_message
from src.rag.ingest import ingest_document
from src.rag.vector_store import list_documents, delete_document
from src.database.conversation_db import (
    init_db,
    get_user_by_api_key,
    revoke_api_credential,
)


logger = logging.getLogger(__name__)

# --------------------------------------------------
# Configuration
# --------------------------------------------------

RATE_LIMIT = 30
RATE_WINDOW = 60

user_requests = defaultdict(deque)
rate_limit_lock = Lock()

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024


security = HTTPBearer(auto_error=False)


# --------------------------------------------------
# API Key Authentication
# --------------------------------------------------

def require_api_key(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> int:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = get_user_by_api_key(credentials.credentials)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    check_rate_limit(user_id)

    return user_id


def check_rate_limit(user_id: int) -> None:
    now = time.monotonic()

    with rate_limit_lock:
        requests = user_requests[user_id]

        while requests and now - requests[0] >= RATE_WINDOW:
            requests.popleft()

        if len(requests) >= RATE_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Try again later.",
            )

        requests.append(now)


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
@app.delete("/credentials")
def revoke_credential(
    user_id: int = Depends(require_api_key),
):
    revoked = revoke_api_credential(user_id)

    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API credential not found",
        )

    return {"message": "API credential revoked successfully"}


# --------------------------------------------------
# Chat Request Model
# --------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: str = Field(min_length=1, max_length=100)

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
    user_id: int = Depends(require_api_key),
):
    answer = process_message(
        user_id=user_id,
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
    user_id: int = Depends(require_api_key),
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
            detail="Only PDF, TXT, and DOCX files are allowed",
        )

    user_upload_dir = UPLOAD_DIR / str(user_id)
    user_upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = user_upload_dir / filename

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
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="File size must not exceed 10 MB",
        )

    try:
        file_path.write_bytes(file_content)

        chunks = ingest_document(str(file_path), user_id)

        return {
            "message": "Document uploaded and indexed successfully",
            "filename": filename,
            "chunks": chunks,
        }

    except Exception as error:
        logger.exception("Document processing failed")

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
    user_id: int = Depends(require_api_key),
):
    return {
        "documents": list_documents(user_id),
    }


# --------------------------------------------------
# Delete Document Endpoint
# --------------------------------------------------

@app.delete("/documents/{filename}")
def remove_document(
    filename: str,
    user_id: int = Depends(require_api_key),
):
    if Path(filename).name != filename or filename in {".", ".."}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename",
        )

    file_path = UPLOAD_DIR / str(user_id) / filename

    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    try:
        delete_document(filename, user_id)
        file_path.unlink()

        return {
            "message": "Document deleted successfully",
            "filename": filename,
        }

    except Exception as error:
        logger.exception("Document deletion failed")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document deletion failed",
        ) from error
