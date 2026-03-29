"""
RAG Engine — handles document ingestion, vector storage, and query answering.
Uses LangChain + ChromaDB + Google Gemini.
"""
import os
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
import chromadb

from .config import (
    GOOGLE_API_KEY,
    UPLOAD_DIR,
    CHROMA_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    EMBEDDING_MODEL,
    LLM_MODEL,
    COLLECTION_NAME,
)

# ─── METADATA TRACKING ──────────────────────────────────────────────────────
METADATA_FILE = CHROMA_DIR / "doc_metadata.json"


def _load_metadata() -> Dict[str, Any]:
    if METADATA_FILE.exists():
        return json.loads(METADATA_FILE.read_text(encoding="utf-8"))
    return {}


def _save_metadata(meta: Dict[str, Any]):
    METADATA_FILE.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def _file_hash(filepath: str) -> str:
    return hashlib.md5(Path(filepath).read_bytes()).hexdigest()


# ─── CHROMA CLIENT ───────────────────────────────────────────────────────────
_chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))


def _get_embeddings():
    return GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=GOOGLE_API_KEY,
    )


def _get_collection():
    return _chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _get_llm():
    return ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.3,
        convert_system_message_to_human=True,
        max_retries=0,
    )


# ─── INGESTION ───────────────────────────────────────────────────────────────
def ingest_document(filepath: str, original_filename: str) -> Dict[str, Any]:
    """
    Load a PDF or text file, chunk it, embed it, and store in ChromaDB.
    Returns metadata about the ingested document.
    """
    ext = Path(filepath).suffix.lower()

    # Load document
    if ext == ".pdf":
        loader = PyPDFLoader(filepath)
    elif ext in (".txt", ".md", ".csv"):
        loader = TextLoader(filepath, encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    raw_docs = loader.load()

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(raw_docs)

    if not chunks:
        raise ValueError("No content could be extracted from the file.")

    # Generate document ID
    doc_id = _file_hash(filepath)

    # Embed and store
    embeddings = _get_embeddings()
    collection = _get_collection()

    ids = []
    documents = []
    metadatas = []
    embed_texts = []

    for i, chunk in enumerate(chunks):
        chunk_id = f"{doc_id}_chunk_{i}"
        ids.append(chunk_id)
        documents.append(chunk.page_content)
        metadatas.append({
            "doc_id": doc_id,
            "filename": original_filename,
            "chunk_index": i,
            "source": chunk.metadata.get("source", filepath),
            "page": chunk.metadata.get("page", 0),
        })
        embed_texts.append(chunk.page_content)

    # Batch embed
    vectors = embeddings.embed_documents(embed_texts)

    # Upsert into ChromaDB
    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=vectors,
    )

    # Save metadata
    meta = _load_metadata()
    meta[doc_id] = {
        "filename": original_filename,
        "chunk_count": len(chunks),
        "file_path": filepath,
    }
    _save_metadata(meta)

    return {
        "doc_id": doc_id,
        "filename": original_filename,
        "chunks": len(chunks),
        "status": "indexed",
    }


# ─── QUERYING ────────────────────────────────────────────────────────────────
RAG_PROMPT = PromptTemplate(
    template="""You are an expert AI research assistant. You will be provided with context from the user's uploaded documents, along with their question and recent conversation history.

Your goal is to answer the question logically and comprehensively. 
1. If the question asks for specific details from the documents, use the provided DOCUMENT CONTEXT.
2. If the question asks for logical deductions, industry standards, comparisons, or general knowledge (e.g., "Is this a good salary?", "What is standard for this role?"), you MUST use your own general expert knowledge to answer, while referencing the document facts where appropriate. 
3. Do NOT simply say "the context doesn't contain this information" if you can answer it using your own knowledge. Be helpful and analytical!

PREVIOUS CHAT HISTORY:
{history}

DOCUMENT CONTEXT:
{context}

CURRENT QUESTION: {question}

Provide a clear, well-structured, and helpful answer. If mentioning facts from the context, you can optionally mention the document sources.""",
    input_variables=["context", "history", "question"],
)


def query_documents(question: str, n_results: int = 5, doc_id: str = None, history: List[Dict[str, str]] = None) -> Dict[str, Any]:
    if history is None:
        history = []
    """
    Query the vector store and generate an AI answer using RAG.
    Returns the answer plus source chunks used.
    """
    collection = _get_collection()

    if collection.count() == 0:
        return {
            "answer": "No documents have been uploaded yet. Please upload some documents first.",
            "sources": [],
        }

    embeddings = _get_embeddings()
    query_vector = embeddings.embed_query(question)

    query_kwargs = {
        "query_embeddings": [query_vector],
        "n_results": min(n_results, collection.count()),
        "include": ["documents", "metadatas", "distances"],
    }
    if doc_id:
        query_kwargs["where"] = {"doc_id": doc_id}

    results = collection.query(**query_kwargs)

    # Build context from retrieved chunks
    context_parts = []
    sources = []
    seen_sources = set()

    for i, (doc, meta, dist) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    )):
        context_parts.append(f"[Source: {meta['filename']}, Page {meta.get('page', '?')}]\n{doc}")
        source_key = f"{meta['filename']}:p{meta.get('page', '?')}"
        if source_key not in seen_sources:
            seen_sources.add(source_key)
            sources.append({
                "filename": meta["filename"],
                "page": meta.get("page", 0),
                "relevance": round(1 - dist, 3),  # cosine distance → similarity
                "preview": doc[:200] + "..." if len(doc) > 200 else doc,
            })

    context = "\n\n---\n\n".join(context_parts)

    # Format history into a string
    history_str = ""
    for msg in history[-4:]: # Use up to last 4 messages
        role = "User" if msg["role"] == "user" else "Assistant"
        history_str += f"{role}: {msg['content']}\n\n"

    # Generate answer with LLM
    llm = _get_llm()
    prompt = RAG_PROMPT.format(context=context, history=history_str, question=question)
    response = llm.invoke(prompt)

    return {
        "answer": response.content,
        "sources": sources,
    }


# ─── DOCUMENT MANAGEMENT ────────────────────────────────────────────────────
def list_documents() -> List[Dict[str, Any]]:
    """List all indexed documents."""
    meta = _load_metadata()
    docs = []
    for doc_id, info in meta.items():
        docs.append({
            "doc_id": doc_id,
            "filename": info["filename"],
            "chunk_count": info["chunk_count"],
        })
    return docs


def delete_document(doc_id: str) -> bool:
    """Delete a document and all its chunks from the vector store."""
    meta = _load_metadata()
    if doc_id not in meta:
        return False

    collection = _get_collection()
    info = meta[doc_id]

    # Delete chunks from ChromaDB
    chunk_ids = [f"{doc_id}_chunk_{i}" for i in range(info["chunk_count"])]
    try:
        collection.delete(ids=chunk_ids)
    except Exception:
        pass  # Chunks may not exist if partially ingested

    # Delete uploaded file
    try:
        os.remove(info["file_path"])
    except FileNotFoundError:
        pass

    # Remove metadata
    del meta[doc_id]
    _save_metadata(meta)

    return True


def get_stats() -> Dict[str, Any]:
    """Get vector store statistics."""
    collection = _get_collection()
    meta = _load_metadata()
    return {
        "total_documents": len(meta),
        "total_chunks": collection.count(),
        "documents": list_documents(),
    }
