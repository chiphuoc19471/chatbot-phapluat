"""
Entry point cho Backend gọi.
Sử dụng:
    from rag.pipeline import answer
    result = answer(query="...", chat_history=[...])
"""
from rag.guardrail import is_labor_law, get_refusal_response
from rag.rewriter import rewrite_query
from rag.retriever import retrieve
from rag.reranker import rerank
from rag.generator import generate

_NOT_FOUND = {
    "answer": "Xin lỗi, tôi không tìm thấy thông tin phù hợp trong cơ sở dữ liệu pháp luật.",
    "sources": [],
}


def answer(query: str, chat_history: list[dict] | None = None) -> dict:
    """
    Args:
        query:        câu hỏi của người dùng
        chat_history: [{"role": "user"/"assistant", "content": "..."}]
                      tối đa 5 lượt gần nhất, Backend truy xuất từ SQLite và truyền vào.

    Returns:
        {
            "answer": str,
            "sources": [{"dieu", "ten_dieu", "van_ban", "trich_doan"}]
        }
    """
    if chat_history is None:
        chat_history = []

    rewritten = rewrite_query(query, chat_history)

    if not is_labor_law(rewritten):
        return get_refusal_response()
    parents = retrieve(rewritten)

    if not parents:
        return _NOT_FOUND

    reranked = rerank(rewritten, parents)
    return generate(query, reranked)
