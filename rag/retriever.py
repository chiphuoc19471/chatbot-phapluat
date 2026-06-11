"""
Parent Document Retrieval:
1. Tìm child chunks bằng similarity search trên Chroma
2. Ánh xạ child → parent (toàn văn Điều) qua parent_id
3. Dedup: mỗi Điều chỉ trả về 1 lần
"""
import json
from langchain_chroma import Chroma
from rag.config import VECTOR_STORE_DIR, DOCSTORE_PATH, TOP_K_RETRIEVE
from rag.embedder import get_embedder

_vectorstore = None
_docstore = None


def _get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = Chroma(
            persist_directory=VECTOR_STORE_DIR,
            embedding_function=get_embedder(),
            collection_name="law_chunks",
        )
    return _vectorstore


def _get_docstore() -> dict:
    global _docstore
    if _docstore is None:
        with open(DOCSTORE_PATH, "r", encoding="utf-8") as f:
            _docstore = json.load(f)
    return _docstore


def retrieve(query: str) -> list[dict]:
    vs = _get_vectorstore()
    docstore = _get_docstore()

    child_results = vs.similarity_search(query, k=TOP_K_RETRIEVE)

    seen = set()
    parents = []
    for child in child_results:
        pid = child.metadata.get("parent_id")
        if pid and pid not in seen and pid in docstore:
            seen.add(pid)
            parents.append(docstore[pid])

    return parents
