from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .ai import generate_chat_reply
from .auth import COOKIE_NAME, create_access_token, get_current_user, hash_password, verify_password
from .db import (
    create_document,
    create_user,
    delete_document,
    get_document,
    get_user_by_email,
    init_db,
    list_documents,
    update_document,
)
from .schemas import (
    AuthUser,
    ChatMessageRequest,
    ChatMessageResponse,
    DocumentCreate,
    DocumentResponse,
    DocumentUpdate,
    SigninRequest,
    SignupRequest,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Reset DB each container run per project requirements.
    init_db(reset=True)
    yield


app = FastAPI(title="Prelegal API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/signup", response_model=AuthUser)
def signup(payload: SignupRequest, response: Response) -> AuthUser:
    if get_user_by_email(payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    user = create_user(payload.email, hash_password(payload.password))
    token = create_access_token(user["id"])
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 24,
    )
    return AuthUser(**user)


@app.post("/api/auth/signin", response_model=AuthUser)
def signin(payload: SigninRequest, response: Response) -> AuthUser:
    user = get_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(user["id"])
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 24,
    )
    return AuthUser(id=user["id"], email=user["email"])


@app.post("/api/auth/signout")
def signout(response: Response) -> dict[str, str]:
    response.delete_cookie(COOKIE_NAME)
    return {"status": "signed_out"}


@app.get("/api/auth/me", response_model=AuthUser)
def me(user: dict = Depends(get_current_user)) -> AuthUser:
    return AuthUser(**user)


@app.get("/api/documents", response_model=list[DocumentResponse])
def documents(user: dict = Depends(get_current_user)) -> list[DocumentResponse]:
    return [DocumentResponse(**doc) for doc in list_documents(user["id"])]


@app.post("/api/documents", response_model=DocumentResponse)
def create_doc(payload: DocumentCreate, user: dict = Depends(get_current_user)) -> DocumentResponse:
    doc = create_document(user["id"], payload.title, payload.doc_type, payload.content)
    return DocumentResponse(**doc)


@app.get("/api/documents/{doc_id}", response_model=DocumentResponse)
def get_doc(doc_id: int, user: dict = Depends(get_current_user)) -> DocumentResponse:
    doc = get_document(doc_id, user["id"])
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentResponse(**doc)


@app.put("/api/documents/{doc_id}", response_model=DocumentResponse)
def update_doc(
    doc_id: int,
    payload: DocumentUpdate,
    user: dict = Depends(get_current_user),
) -> DocumentResponse:
    doc = update_document(
        doc_id,
        user["id"],
        title=payload.title,
        doc_type=payload.doc_type,
        content=payload.content,
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentResponse(**doc)


@app.delete("/api/documents/{doc_id}")
def delete_doc(doc_id: int, user: dict = Depends(get_current_user)) -> dict[str, str]:
    if not delete_document(doc_id, user["id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return {"status": "deleted"}


@app.get("/api/chat/greeting")
def chat_greeting() -> dict[str, str]:
    return {
        "message": (
            "Hi, I can help draft your agreement. "
            "Tell me what document you want to create and key details."
        )
    }


@app.post("/api/chat/message", response_model=ChatMessageResponse)
def chat_message(payload: ChatMessageRequest) -> ChatMessageResponse:
    result = generate_chat_reply(
        message=payload.message,
        conversation=payload.conversation,
        doc_type=payload.doc_type,
        known_fields=payload.known_fields,
    )
    return ChatMessageResponse(**result)


frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(frontend_dist / "index.html")
