import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models.user import User
from models.conversation import Conversation, Message
from auth import get_current_user

router = APIRouter(prefix="/chat", tags=["Chat & RAG"])

# --- Pydantic Schemas ---

class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[int] = None

class SourceInfo(BaseModel):
    law: str
    article: str
    chapter: Optional[str] = None
    content: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceInfo]
    conversation_id: int
    message_id: int


# --- Mock RAG Service ---

class MockRAGService:
    @staticmethod
    def get_answer(question: str) -> Dict[str, Any]:
        """
        Simulates RAG Pipeline and returns an answer along with relevant sources.
        """
        q_lower = question.lower()
        
        # Scenario 1: Probation (Thử việc)
        if "thử việc" in q_lower or "thu viec" in q_lower:
            return {
                "answer": (
                    "Theo **Điều 25, Bộ luật Lao động 2019**, thời gian thử việc tối đa được quy định như sau:\n\n"
                    "1. Không quá **180 ngày** đối với công việc của người quản lý doanh nghiệp theo quy định của Luật Doanh nghiệp.\n"
                    "2. Không quá **60 ngày** đối với công việc có chức danh nghề cần trình độ chuyên môn, kỹ thuật từ cao đẳng trở lên.\n"
                    "3. Không quá **30 ngày** đối với công việc có chức danh nghề cần trình độ chuyên môn, kỹ thuật trung cấp, công nhân kỹ thuật, nhân viên nghiệp vụ.\n"
                    "4. Không quá **06 ngày làm việc** đối với công việc khác."
                ),
                "sources": [
                    {
                        "law": "Bộ luật Lao động 2019",
                        "article": "Điều 25",
                        "chapter": "Chương III",
                        "content": "Thời gian thử việc tối đa đối với từng loại hình lao động..."
                    }
                ]
            }
            
        # Scenario 2: Salary and Bonuses (Lương, thưởng)
        elif any(k in q_lower for k in ["lương", "luong", "thưởng", "thuong", "phụ cấp", "phu cap"]):
            return {
                "answer": (
                    "Dựa trên các quy định về Tiền lương và Thưởng trong **Bộ luật Lao động 2019**:\n\n"
                    "* **Tiền lương (Điều 90):** Tiền lương là số tiền mà người sử dụng lao động trả cho người lao động theo thỏa thuận để thực hiện công việc. Mức lương này không được thấp hơn mức lương tối thiểu vùng do Chính phủ công bố.\n"
                    "* **Thưởng (Điều 104):** Thưởng là số tiền hoặc tài sản hoặc bằng các hình thức khác mà người sử dụng lao động thưởng cho người lao động căn cứ vào kết quả sản xuất, kinh doanh và mức độ hoàn thành công việc."
                ),
                "sources": [
                    {
                        "law": "Bộ luật Lao động 2019",
                        "article": "Điều 90",
                        "chapter": "Chương VI",
                        "content": "Quy định chung về tiền lương của người lao động..."
                    },
                    {
                        "law": "Bộ luật Lao động 2019",
                        "article": "Điều 104",
                        "chapter": "Chương VI",
                        "content": "Quy chế thưởng do người sử dụng lao động quyết định sau khi tham khảo ý kiến ban đại diện..."
                    }
                ]
            }
            
        # Scenario 3: Leave (Nghỉ phép)
        elif any(k in q_lower for k in ["nghỉ phép", "nghi phep", "nghỉ lễ", "nghi le", "phép năm", "phep nam"]):
            return {
                "answer": (
                    "Quy định về nghỉ phép hằng năm theo **Điều 113, Bộ luật Lao động 2019**:\n\n"
                    "Người lao động làm việc đủ 12 tháng cho một người sử dụng lao động thì được nghỉ hằng năm, hưởng nguyên lương theo hợp đồng lao động như sau:\n"
                    "- **12 ngày làm việc** đối với người làm công việc trong điều kiện bình thường.\n"
                    "- **14 ngày làm việc** đối với người lao động chưa thành niên, lao động là người khuyết tật hoặc người làm nghề, công việc nặng nhọc, độc hại, nguy hiểm.\n"
                    "- Cứ **đủ 05 năm làm việc** thì số ngày nghỉ hằng năm được tăng thêm tương ứng **01 ngày**."
                ),
                "sources": [
                    {
                        "law": "Bộ luật Lao động 2019",
                        "article": "Điều 113",
                        "chapter": "Chương VII",
                        "content": "Nghỉ hằng năm và chế độ thanh toán tiền lương nghỉ phép năm..."
                    }
                ]
            }

        # Scenario 4: Insurance (Bảo hiểm)
        elif any(k in q_lower for k in ["bảo hiểm", "bao hiem", "bhxh", "thai sản", "thai san"]):
            return {
                "answer": (
                    "Về chế độ bảo hiểm xã hội (BHXH) và Thai sản:\n\n"
                    "Người lao động và người sử dụng lao động phải tham gia BHXH bắt buộc, bảo hiểm y tế (BHYT), bảo hiểm thất nghiệp (BHTN).\n"
                    "- **Thai sản:** Lao động nữ sinh con được nghỉ chế độ thai sản trước và sau khi sinh con là **06 tháng** (thời gian nghỉ trước sinh không quá 02 tháng). Trong thời gian này, người lao động được hưởng trợ cấp thai sản do Quỹ BHXH chi trả."
                ),
                "sources": [
                    {
                        "law": "Luật Bảo hiểm xã hội 2014",
                        "article": "Điều 34",
                        "chapter": "Chương III",
                        "content": "Thời gian hưởng chế độ khi sinh con đối với lao động nam và nữ..."
                    }
                ]
            }

        # Scenario 5: Dispute and Dismissal (Sa thải, tranh chấp)
        elif any(k in q_lower for k in ["sa thải", "sa thai", "đuổi việc", "duoi viec", "tranh chấp", "tranh chap", "thôi việc", "thoi viec"]):
            return {
                "answer": (
                    "Về chấm dứt hợp đồng lao động và kỷ luật sa thải:\n\n"
                    "- **Đơn phương chấm dứt hợp đồng:** Người lao động có quyền đơn phương chấm dứt hợp đồng lao động nhưng phải báo trước ít nhất **45 ngày** đối với hợp đồng không xác định thời hạn, ít nhất **30 ngày** đối với hợp đồng xác định thời hạn từ 12-36 tháng.\n"
                    "- **Kỷ luật sa thải (Điều 125):** Chỉ được áp dụng trong các trường hợp nghiêm trọng như trộm cắp, tham ô, tiết lộ bí mật công nghệ, kinh doanh, tự ý bỏ việc 05 ngày cộng dồn trong 30 ngày mà không có lý do chính đáng."
                ),
                "sources": [
                    {
                        "law": "Bộ luật Lao động 2019",
                        "article": "Điều 125",
                        "chapter": "Chương VIII",
                        "content": "Áp dụng hình thức xử lý kỷ luật sa thải..."
                    }
                ]
            }

        # Default Scenario
        else:
            return {
                "answer": (
                    "Cảm ơn bạn đã đặt câu hỏi. Đây là câu trả lời tự động hỗ trợ tư vấn pháp luật lao động.\n\n"
                    "Vui lòng đặt các câu hỏi cụ thể hơn liên quan đến **thử việc**, **tiền lương**, **nghỉ phép**, **bảo hiểm** hoặc **kỷ luật sa thải** để nhận được thông tin chi tiết và chính xác từ Bộ luật Lao động Việt Nam."
                ),
                "sources": [
                    {
                        "law": "Bộ luật Lao động 2019",
                        "article": "Điều 5",
                        "chapter": "Chương I",
                        "content": "Quyền và nghĩa vụ cơ bản của người lao động..."
                    }
                ]
            }


def classify_topic(question: str) -> str:
    """Helper to classify conversation topic based on simple keyword parsing."""
    q_lower = question.lower()
    if "thử việc" in q_lower or "thu viec" in q_lower or "hợp đồng" in q_lower or "hop dong" in q_lower:
        return "hop-dong"
    elif any(k in q_lower for k in ["lương", "luong", "thưởng", "thuong", "phụ cấp", "phu cap"]):
        return "luong"
    elif any(k in q_lower for k in ["nghỉ phép", "nghi phep", "nghỉ lễ", "nghi le", "phép năm", "phep nam"]):
        return "nghi-phep"
    elif any(k in q_lower for k in ["bảo hiểm", "bao hiem", "bhxh", "thai sản", "thai san"]):
        return "bhxh"
    elif any(k in q_lower for k in ["sa thải", "sa thai", "đuổi việc", "duoi viec", "tranh chấp", "tranh chap", "thôi việc", "thoi viec"]):
        return "tranh-chap"
    else:
        return "khac"


# --- Endpoints ---

@router.post("", response_model=ChatResponse, status_code=status.HTTP_200_OK)
def send_question(
    chat_req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Handles user chat messages.
    Creates a new conversation if conversation_id is not provided.
    Saves both the user's question and the assistant's generated response in SQLite database.
    """
    conversation = None
    
    # 1. Resolve or Create Conversation
    if chat_req.conversation_id:
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == chat_req.conversation_id)
            .first()
        )
        if not conversation or conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy hội thoại"
            )
    else:
        # Create a new conversation using the first 50 chars of the question as the title
        title = chat_req.question[:50] + "..." if len(chat_req.question) > 50 else chat_req.question
        topic = classify_topic(chat_req.question)
        conversation = Conversation(
            user_id=current_user.id,
            title=title,
            topic=topic
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # 2. Save User's Message
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=chat_req.question,
        sources=None
    )
    db.add(user_msg)
    
    # 3. Call Mock RAG Service for Answer
    rag_result = MockRAGService.get_answer(chat_req.question)
    answer = rag_result["answer"]
    sources = rag_result["sources"]
    
    # 4. Save Assistant's Message (Sources serialized as JSON string)
    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
        sources=json.dumps(sources, ensure_ascii=False)
    )
    db.add(assistant_msg)
    
    # 5. Update Conversation timestamp
    conversation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(assistant_msg)
    
    # 6. Parse sources to correct format for response model
    sources_response = [
        SourceInfo(
            law=s["law"],
            article=s["article"],
            chapter=s.get("chapter"),
            content=s.get("content")
        )
        for s in sources
    ]
    
    return ChatResponse(
        answer=answer,
        sources=sources_response,
        conversation_id=conversation.id,
        message_id=assistant_msg.id
    )
