"""
LLM Reranker: dùng GPT-4.1-mini để chọn các Điều luật liên quan nhất
trong danh sách parent documents sau khi retrieve.
"""
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from rag.config import OPENAI_API_KEY, LLM_MODEL, TOP_N_RERANK

_llm = None

_SYSTEM = (
    "Bạn là chuyên gia pháp luật lao động Việt Nam. "
    f"Nhiệm vụ: chọn tối đa {TOP_N_RERANK} điều luật liên quan nhất đến câu hỏi, "
    "theo thứ tự liên quan giảm dần. "
    "Chỉ trả về JSON array chứa các index (ví dụ: [2, 0, 5, 3]), không giải thích."
)


def _get_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model=LLM_MODEL,
            openai_api_key=OPENAI_API_KEY,
            temperature=0,
        )
    return _llm


def rerank(query: str, parents: list[dict]) -> list[dict]:
    if len(parents) <= TOP_N_RERANK:
        return parents

    candidates_text = "\n\n".join(
        f"[{i}] {p.get('dieu', '')}: {p['text'][:400]}"
        for i, p in enumerate(parents)
    )

    user_prompt = (
        f"Câu hỏi: {query}\n\n"
        f"Các điều luật ứng viên:\n{candidates_text}\n\n"
        f"Chọn {TOP_N_RERANK} điều luật liên quan nhất (JSON array các index):"
    )

    response = _get_llm().invoke([
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=user_prompt),
    ])

    try:
        content = response.content.strip()
        start, end = content.find("["), content.rfind("]") + 1
        indices = json.loads(content[start:end])
        selected = [parents[i] for i in indices if 0 <= i < len(parents)]
        return selected[:TOP_N_RERANK]
    except Exception:
        return parents[:TOP_N_RERANK]
