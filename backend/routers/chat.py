import json
import asyncio
import traceback
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, SessionLocal
from models.user import User
from models.conversation import Conversation, Message
from auth import get_current_user
from rag.pipeline import answer as rag_answer
from rag.guardrail import is_labor_law, get_refusal_response
from rag.rewriter import rewrite_query
from rag.retriever import retrieve
from rag.reranker import rerank
from rag.generator import astream_generate, build_sources

router = APIRouter(prefix="/chat", tags=["Chat & RAG"])


@router.get("/ping-stream")
async def ping_stream():
    """Test SSE cơ bản – không cần auth, không cần RAG."""
    async def gen():
        for i in range(3):
            yield f"data: {json.dumps({'ping': i})}\n\n"
            await asyncio.sleep(0.2)
        yield f"data: {json.dumps({'done': True})}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

# --- Pydantic Schemas ---

class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[int] = None

class SourceInfo(BaseModel):
    dieu: str
    ten_dieu: str
    van_ban: str
    trich_doan: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceInfo]
    conversation_id: int
    message_id: int



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
        conversation = Conversation(
            user_id=current_user.id,
            title=title,
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
    
    # 3. Lấy lịch sử hội thoại (tối đa 5 lượt gần nhất) để truyền vào RAG
    recent_messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.id.desc())
        .limit(10)
        .all()
    )
    chat_history = [
        {"role": m.role, "content": m.content}
        for m in reversed(recent_messages)
    ]

    # 4. Gọi RAG pipeline thật
    rag_result = rag_answer(query=chat_req.question, chat_history=chat_history)
    answer = rag_result["answer"]
    sources = rag_result["sources"]

    # 5. Save Assistant's Message (Sources serialized as JSON string)
    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
        sources=json.dumps(sources, ensure_ascii=False)
    )
    db.add(assistant_msg)

    # 6. Update Conversation timestamp
    conversation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(assistant_msg)

    # 7. Parse sources to correct format for response model
    sources_response = [
        SourceInfo(
            dieu=s["dieu"],
            ten_dieu=s["ten_dieu"],
            van_ban=s["van_ban"],
            trich_doan=s["trich_doan"],
        )
        for s in sources
    ]
    
    return ChatResponse(
        answer=answer,
        sources=sources_response,
        conversation_id=conversation.id,
        message_id=assistant_msg.id
    )


@router.post("/stream")
async def send_question_stream(
    chat_req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Streaming endpoint: RAG chạy trong thread, sau đó stream kết quả từng từ."""
    print(f"[STREAM] nhận câu hỏi: {chat_req.question[:60]}")

    # 1. Resolve / create conversation
    if chat_req.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == chat_req.conversation_id
        ).first()
        if not conversation or conversation.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Không tìm thấy hội thoại")
    else:
        title = chat_req.question[:50] + ("..." if len(chat_req.question) > 50 else "")
        conversation = Conversation(user_id=current_user.id, title=title)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # 2. Save user message
    db.add(Message(conversation_id=conversation.id, role="user", content=chat_req.question))
    db.commit()

    # 3. Lấy lịch sử hội thoại
    recent = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.id.desc()).limit(10).all()
    chat_history = [{"role": m.role, "content": m.content} for m in reversed(recent)]

    conv_id = conversation.id
    question_copy = chat_req.question

    # 4. Chạy toàn bộ RAG pipeline trong thread (dùng hàm sync đã hoạt động)
    def _run_rag_and_save():
        try:
            result = rag_answer(query=question_copy, chat_history=chat_history)
            answer = result["answer"]
            sources = result["sources"]
        except Exception:
            traceback.print_exc()
            answer = "Xin lỗi, đã xảy ra lỗi xử lý. Vui lòng thử lại."
            sources = []

        # Lưu assistant message với session mới
        msg_id = None
        try:
            new_db = SessionLocal()
            try:
                msg = Message(
                    conversation_id=conv_id,
                    role="assistant",
                    content=answer,
                    sources=json.dumps(sources, ensure_ascii=False),
                )
                new_db.add(msg)
                new_db.query(Conversation).filter(Conversation.id == conv_id).update(
                    {"updated_at": datetime.utcnow()}
                )
                new_db.commit()
                new_db.refresh(msg)
                msg_id = msg.id
            finally:
                new_db.close()
        except Exception:
            traceback.print_exc()

        print(f"[STREAM] RAG xong, msg_id={msg_id}, độ dài={len(answer)}")
        return answer, sources, msg_id

    answer, sources, msg_id = await asyncio.get_running_loop().run_in_executor(
        None, _run_rag_and_save
    )

    # 5. Stream kết quả từng từ
    import re
    tokens = re.split(r'(\s+)', answer)   # giữ nguyên khoảng trắng

    async def event_stream():
        yield f"data: {json.dumps({'status': 'generating'}, ensure_ascii=False)}\n\n"
        for tok in tokens:
            if tok:
                yield f"data: {json.dumps({'token': tok}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.012)
        yield f"data: {json.dumps({'done': True, 'sources': sources, 'conversation_id': conv_id, 'message_id': msg_id}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
