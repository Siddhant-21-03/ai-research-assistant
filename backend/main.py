"""
FastAPI backend for the AI Research Assistant.
Provides endpoints for document upload, querying, and management.
"""
import os
import shutil
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import UPLOAD_DIR
from .rag_engine import ingest_document, query_documents, list_documents, delete_document, get_stats

app = FastAPI(
    title="AI Research Assistant",
    description="RAG-powered research assistant API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── MODELS ──────────────────────────────────────────────────────────────────
class MessageContext(BaseModel):
    role: str
    content: str

class QueryRequest(BaseModel):
    question: str
    n_results: int = 5
    doc_id: str | None = None
    history: list[MessageContext] = []


class QueryResponse(BaseModel):
    answer: str
    sources: list


# ─── ENDPOINTS ───────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "AI Research Assistant API", "status": "running"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a PDF or text file for indexing."""
    allowed_extensions = {".pdf", ".txt", ".md", ".csv"}
    ext = Path(file.filename).suffix.lower()

    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(allowed_extensions)}",
        )

    # Save uploaded file
    save_path = str(UPLOAD_DIR / file.filename)
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        result = ingest_document(save_path, file.filename)
        return result
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        traceback.print_exc()
        # Clean up on failure
        if os.path.exists(save_path):
            os.remove(save_path)
        raise HTTPException(status_code=500, detail=f"Upload Error: {str(e)}\n\n{err_msg}")


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Ask a question about uploaded documents."""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        req_history = [{"role": m.role, "content": m.content} for m in request.history]
        result = query_documents(
            request.question, 
            n_results=request.n_results, 
            doc_id=request.doc_id,
            history=req_history
        )
        return result
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Query Error: {str(e)}\n\n{err_msg}")


@app.get("/documents")
def documents():
    """List all uploaded and indexed documents."""
    return list_documents()


@app.delete("/documents/{doc_id}")
def remove_document(doc_id: str):
    """Delete a document and its vectors."""
    success = delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"status": "deleted", "doc_id": doc_id}


@app.get("/stats")
def stats():
    """Get vector store statistics."""
    return get_stats()
