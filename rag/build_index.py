"""
Build Chroma index (chunk con) + docstore JSON (chunk cha).
Chạy 1 lần, hoặc khi data/chunks/ thay đổi:
    python -m rag.build_index
"""
import os
import json
import glob
from langchain_chroma import Chroma
from langchain_core.documents import Document
from rag.config import VECTOR_STORE_DIR, DOCSTORE_PATH, CHUNKS_DIR
from rag.embedder import get_embedder


def load_all_chunks() -> list[dict]:
    chunks = []
    json_files = glob.glob(os.path.join(CHUNKS_DIR, "*.json"))
    if not json_files:
        raise FileNotFoundError(f"Không tìm thấy file JSON nào trong {CHUNKS_DIR}")
    for path in json_files:
        with open(path, "r", encoding="utf-8") as f:
            chunks.extend(json.load(f))
    return chunks


def build_parents(chunks: list[dict]) -> dict[str, dict]:
    """
    Gom nhóm các child chunk theo (Source, Điều) để tạo parent document.
    Key: "{source}_{dieu}", Value: dict chứa text đầy đủ của Điều đó.
    """
    parents: dict[str, dict] = {}
    for chunk in chunks:
        meta = chunk["metadata"]
        source = meta.get("Source", "unknown")
        dieu = meta.get("Điều")
        if not dieu:
            continue
        pid = f"{source}__{dieu}"
        if pid not in parents:
            parents[pid] = {
                "parent_id": pid,
                "dieu": dieu,
                "source": source,
                "chuong": meta.get("Chương", ""),
                "muc": meta.get("Mục", ""),
                "text": chunk["text"],
            }
        else:
            parents[pid]["text"] += "\n" + chunk["text"]
    return parents


def build_child_docs(chunks: list[dict], parents: dict) -> list[Document]:
    """Tạo LangChain Document cho mỗi child chunk, gắn parent_id vào metadata."""
    docs = []
    for chunk in chunks:
        meta = chunk["metadata"]
        source = meta.get("Source", "unknown")
        dieu = meta.get("Điều")
        if not dieu:
            continue
        pid = f"{source}__{dieu}"
        if pid not in parents:
            continue
        docs.append(Document(
            page_content=chunk["text"],
            metadata={
                "chunk_id": str(chunk["chunk_id"]),
                "parent_id": pid,
                "dieu": dieu,
                "source": source,
                "chuong": meta.get("Chương", ""),
                "muc": meta.get("Mục", ""),
            }
        ))
    return docs


def main():
    print("Đang tải chunks từ data/chunks/ ...")
    chunks = load_all_chunks()
    print(f"  Tổng: {len(chunks)} chunks")

    print("Đang tạo parent docstore ...")
    parents = build_parents(chunks)
    print(f"  Tổng: {len(parents)} parent documents (Điều)")

    print("Đang tạo child documents ...")
    child_docs = build_child_docs(chunks, parents)
    print(f"  Tổng: {len(child_docs)} child documents để embedding")

    print("Đang embed và lưu vào Chroma ...")
    Chroma.from_documents(
        documents=child_docs,
        embedding=get_embedder(),
        persist_directory=VECTOR_STORE_DIR,
        collection_name="law_chunks",
    )
    print(f"  Chroma index lưu tại: {VECTOR_STORE_DIR}")

    print("Đang lưu parent docstore ...")
    os.makedirs(os.path.dirname(DOCSTORE_PATH), exist_ok=True)
    with open(DOCSTORE_PATH, "w", encoding="utf-8") as f:
        json.dump(parents, f, ensure_ascii=False, indent=2)
    print(f"  Docstore lưu tại: {DOCSTORE_PATH}")

    print("\nHoàn tất! Index và docstore đã sẵn sàng.")


if __name__ == "__main__":
    main()
