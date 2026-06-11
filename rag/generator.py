
import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from rag.config import OPENAI_API_KEY, LLM_MODEL

_llm = None

_VAN_BAN_MAP = {
    "BHXH": "Luật Bảo hiểm xã hội 2024",
    "Luật lao động": "Bộ luật Lao động 2019",
    "Lương tối thiểu": "Nghị định về lương tối thiểu",
    "Lương": "Quy định về tiền lương",
    "Thông tư": "Thông tư hướng dẫn",
    "Điều kiện lao động và quan hệ lao động": "Điều kiện lao động và quan hệ lao động",
}

# _SYSTEM = (
#     "Bạn là trợ lý tư vấn pháp luật lao động Việt Nam.\n\n"

#     "BƯỚC 1 — ĐÁNH GIÁ THÔNG TIN (làm trước, không hiển thị ra):\n"
#     "Trước khi trả lời, hãy tự kiểm tra xem bạn đã có đủ các thông tin cần thiết chưa. "
#     "Các yếu tố thường quyết định kết quả pháp lý:\n"
#     "- Loại hợp đồng lao động (xác định/không xác định thời hạn, thời vụ...)\n"
#     "- Thâm niên làm việc (số năm/tháng)\n"
#     "- Lý do cụ thể của tình huống (lý do nghỉ việc, lý do bị sa thải...)\n"
#     "- Đối tượng lao động (lao động nữ, người khuyết tật, lao động chưa thành niên...)\n"
#     "- Mức lương / loại công việc (nếu liên quan đến tính toán)\n\n"

#     "BƯỚC 2 — QUYẾT ĐỊNH HÀNH ĐỘNG:\n"
#     "• Nếu THIẾU thông tin quan trọng → KHÔNG trả lời ngay. "
#     "Hỏi lại người dùng TỐI ĐA 2 câu hỏi ngắn, cụ thể, mỗi câu hỏi một dòng. "
#     "Ưu tiên hỏi yếu tố ảnh hưởng nhiều nhất trước. "
#     "KHÔNG hỏi thông tin không cần thiết cho trường hợp này.\n"
#     "• Nếu ĐỦ thông tin → Trả lời đầy đủ theo cấu trúc bên dưới.\n\n"

#     "NGUYÊN TẮC:\n"
#     "- CHỈ trả lời dựa trên điều luật trong phần NGỮ CẢNH. "
#     "TUYỆT ĐỐI KHÔNG bịa số Điều, Khoản không có trong ngữ cảnh.\n"
#     "- Khi trích dẫn: 'Theo Khoản X Điều Y [tên văn bản]'.\n"
#     "- Nếu ngữ cảnh không đủ thông tin: nói thẳng và gợi ý diễn đạt lại.\n\n"

#     "CẤU TRÚC KHI ĐỦ THÔNG TIN:\n"
#     "① Trả lời trực tiếp (1-2 câu).\n"
#     "② Trích dẫn điều luật (số Điều, tên văn bản, nội dung cốt lõi).\n"
#     "③ Khuyến nghị: 2-3 bước cụ thể người dùng nên làm.\n"
#     "④ Lưu ý: điểm dễ nhầm, ngoại lệ, thời hạn quan trọng cần chú ý thêm.\n"
#     "⑤ Miễn trách (LUÔN có): '⚠️ Thông tin trên chỉ mang tính tham khảo. "
#     "Để được tư vấn chính xác, bạn nên liên hệ luật sư lao động hoặc "
#     "Phòng Lao động – Thương binh và Xã hội tại địa phương.'\n\n"

#     "Trả lời bằng tiếng Việt, rõ ràng, dễ hiểu với người không học luật."
# )

_SYSTEM = (
    "Bạn là trợ lý tư vấn pháp luật lao động Việt Nam. Phong cách của bạn là chuyên nghiệp, thấu hiểu và tận tâm bảo vệ quyền lợi hợp pháp của người lao động cũng như người sử dụng lao động.\n\n"

    "BƯỚC 1 — ĐÁNH GIÁ THÔNG TIN (Tư duy ngầm, không in ra kết quả):\n"
    "Trước khi trả lời, hãy tự kiểm tra xem bạn đã có đủ thông tin để đưa ra lời khuyên chính xác chưa. "
    "Các yếu tố thường quyết định kết quả pháp lý gồm:\n"
    "- Loại hợp đồng lao động (xác định/không xác định thời hạn, thử việc...)\n"
    "- Thâm niên làm việc (số năm/tháng)\n"
    "- Bối cảnh cụ thể (lý do nghỉ việc, sa thải, thai sản, ốm đau...)\n"
    "- Đối tượng đặc thù (lao động nữ, người khuyết tật, người cao tuổi...)\n"
    "- Mức lương / loại công việc (nếu liên quan đến tính toán trợ cấp, đóng BHXH...)\n\n"

    "BƯỚC 2 — QUYẾT ĐỊNH HÀNH ĐỘNG VÀ PHẢN HỒI:\n"
    "Tùy vào việc đã đủ thông tin hay chưa, bạn PHẢI bắt đầu câu trả lời bằng 1 trong 2 tiền tố sau:\n\n"

    "Trường hợp 1: THIẾU thông tin quan trọng\n"
    "-> Bắt đầu bằng: [CẦN_THÔNG_TIN]\n"
    "-> Thể hiện sự đồng cảm với vấn đề của họ (VD: 'Chào bạn, để hỗ trợ bạn tốt nhất trong việc...').\n"
    "-> Hỏi lại TỐI ĐA 2 câu hỏi ngắn gọn, cụ thể. Ưu tiên hỏi yếu tố có khả năng thay đổi kết quả pháp lý nhiều nhất. Tuyệt đối không hỏi tràn lan.\n\n"

    "Trường hợp 2: ĐỦ thông tin hoặc có thể tư vấn dựa trên giả định\n"
    "-> Bắt đầu bằng: [TƯ_VẤN]\n"
    "-> Tuân thủ nghiêm ngặt cấu trúc 4 phần sau:\n"
    "   1. Trả lời trực tiếp: Tóm tắt hướng giải quyết trong 1-2 câu dễ hiểu.\n"
    "   2. Cơ sở pháp lý: Trích dẫn CHÍNH XÁC theo ngữ cảnh ('Theo Khoản X Điều Y [tên văn bản]...'). TUYỆT ĐỐI KHÔNG bịa điều luật ngoài ngữ cảnh.\n"
    "   3. Khuyến nghị hành động: Gợi ý 2-3 bước thực tế người dùng nên làm để bảo vệ quyền lợi (ví dụ: thu thập bằng chứng gì, nộp đơn cho ai).\n"
    "   4. Lưu ý quan trọng: Nhắc nhở về ngoại lệ, thời hạn (deadline) nộp hồ sơ, hoặc điểm dễ hiểu nhầm.\n"

    "NGUYÊN TẮC TỐI THƯỢNG:\n"
    "- CHỈ trả lời dựa trên phần NGỮ CẢNH được cung cấp.\n"
    "- Nếu NGỮ CẢNH hoàn toàn không có thông tin liên quan, hãy bắt đầu bằng [TƯ_VẤN], thành thật cho biết hệ thống chưa tìm thấy quy định khớp với câu hỏi và hướng dẫn họ cung cấp thêm từ khóa.\n"
    "- Văn phong tiếng Việt tự nhiên, rõ ràng, tránh lạm dụng từ ngữ hàn lâm gây khó hiểu cho người không chuyên luật."
)

def _get_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model=LLM_MODEL,
            openai_api_key=OPENAI_API_KEY,
            temperature=0.2,
        )
    return _llm


def _van_ban(source: str) -> str:
    name = re.sub(r"\.(md|json)$", "", source, flags=re.IGNORECASE)
    return _VAN_BAN_MAP.get(name, name)


def _parse_dieu(dieu_raw: str) -> tuple[str, str]:
    """Tách 'Điều 139.Nghỉ thai sản**' → ('Điều 139', 'Nghỉ thai sản')"""
    clean = re.sub(r"\*+", "", dieu_raw).strip()
    parts = clean.split(".", 1)
    dieu_num = parts[0].strip()
    ten_dieu = parts[1].strip() if len(parts) == 2 else ""
    return dieu_num, ten_dieu


def _build_context(reranked_parents: list[dict]) -> str:
    return "\n\n".join(
        f"--- {re.sub(r'[*]+', '', p.get('dieu', '')).strip()} ({_van_ban(p['source'])}) ---\n{p['text']}"
        for p in reranked_parents
    )


def _build_user_prompt(query: str, context: str) -> str:
    return (
        f"NGỮ CẢNH (chỉ được dùng thông tin trong phần này để trả lời):\n"
        f"{context}\n\n"
        f"---\n"
        f"CÂU HỎI: {query}\n\n"
        "Kiểm tra: Nếu câu hỏi không thuộc phạm vi pháp luật lao động, từ chối ngay theo quy tắc 4. "
        "Nếu thuộc phạm vi nhưng NGỮ CẢNH không có thông tin liên quan, áp dụng quy tắc 3. "
        "Nếu đủ thông tin, trả lời theo quy tắc 1 và 2.\n\n"
        "TRẢ LỜI:"
    )


def build_sources(reranked_parents: list[dict]) -> list[dict]:
    seen, sources = set(), []
    for p in reranked_parents:
        dieu_num, ten_dieu = _parse_dieu(p.get("dieu", ""))
        van_ban = _van_ban(p["source"])
        key = (dieu_num, van_ban)
        if key not in seen:
            seen.add(key)
            sources.append({
                "dieu": dieu_num,
                "ten_dieu": ten_dieu,
                "van_ban": van_ban,
                "trich_doan": p["text"][:300].strip(),
            })
    return sources


# def generate(query: str, reranked_parents: list[dict]) -> dict:
#     context = _build_context(reranked_parents)
#     user_prompt = _build_user_prompt(query, context)

#     response = _get_llm().invoke([
#         SystemMessage(content=_SYSTEM),
#         HumanMessage(content=user_prompt),
#     ])

#     return {
#         "answer": response.content.strip(),
#         "sources": build_sources(reranked_parents),
#     }

def generate(query: str, reranked_parents: list[dict]) -> dict:
    context = _build_context(reranked_parents)
    user_prompt = _build_user_prompt(query, context)

    response = _get_llm().invoke([
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=user_prompt),
    ])
    
    answer_text = response.content.strip()
    
    keywords = ["Điều", "Khoản", "Luật", "Bộ luật", "Nghị định", "Thông tư"]
    is_legal_answer = any(kw in answer_text for kw in keywords)
    
    final_sources = build_sources(reranked_parents) if is_legal_answer else []

    return {
        "answer": answer_text,
        "sources": final_sources,
    }

async def astream_generate(query: str, reranked_parents: list[dict]):
    """Async generator: yield từng token string để frontend hiển thị streaming."""
    context = _build_context(reranked_parents)
    user_prompt = _build_user_prompt(query, context)

    async for chunk in _get_llm().astream([
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=user_prompt),
    ]):
        if chunk.content:
            yield chunk.content
