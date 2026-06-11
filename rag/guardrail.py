"""
Guardrail: kiểm tra câu hỏi có thuộc phạm vi pháp luật lao động không
TRƯỚC KHI gọi retriever. Nếu không, trả về từ chối ngay.
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from rag.config import OPENAI_API_KEY, LLM_MODEL

_llm = None

_LABOR_LAW_TOPICS = (
    "hợp đồng lao động, tiền lương, lương tối thiểu, phụ cấp, thưởng, "
    "bảo hiểm xã hội (BHXH), bảo hiểm y tế, bảo hiểm thất nghiệp, thai sản, "
    "thời giờ làm việc, giờ làm thêm (残業), nghỉ phép, nghỉ lễ, nghỉ ốm, "
    "kỷ luật lao động, sa thải, chấm dứt hợp đồng, thôi việc, "
    "tranh chấp lao động, đình công, công đoàn, "
    "an toàn vệ sinh lao động, tai nạn lao động, bệnh nghề nghiệp, "
    "người lao động nước ngoài, thử việc, đào tạo nghề"
)

_SYSTEM = (
    "Bạn là bộ lọc chủ đề. Nhiệm vụ duy nhất: xác định câu hỏi có thuộc "
    "phạm vi pháp luật lao động Việt Nam hay không.\n\n"
    f"Phạm vi pháp luật lao động gồm: {_LABOR_LAW_TOPICS}\n\n"
    "Trả lời CHỈ bằng một từ: YES hoặc NO.\n"
    "YES = câu hỏi liên quan đến pháp luật lao động.\n"
    "NO = câu hỏi thuộc lĩnh vực khác (đất đai, hình sự, hôn nhân gia đình, "
    "dân sự, doanh nghiệp, thuế, hành chính, an ninh, y tế, giáo dục...)."
)

_REFUSAL = (
    "Xin lỗi, tôi chỉ hỗ trợ các câu hỏi liên quan đến **pháp luật lao động** "
    "như: hợp đồng lao động, tiền lương, bảo hiểm xã hội, nghỉ phép, "
    "kỷ luật sa thải, tranh chấp lao động,...\n\n"
    "Câu hỏi của bạn thuộc lĩnh vực khác, vui lòng liên hệ chuyên gia phù hợp."
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


def is_labor_law(query: str) -> bool:
    response = _get_llm().invoke([
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=query),
    ])
    return response.content.strip().upper().startswith("YES")


def get_refusal_response() -> dict:
    return {"answer": _REFUSAL, "sources": []}
