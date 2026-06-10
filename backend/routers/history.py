import json
from datetime import datetime
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from database import get_db
from models.user import User
from models.conversation import Conversation, Message
from auth import get_current_user

router = APIRouter(prefix="/history", tags=["Chat History"])

# --- Pydantic Schemas ---

class ConversationSummaryResponse(BaseModel):
    id: int
    title: str
    topic: str
    message_count: int
    created_at: datetime
    updated_at: datetime

class MessageDetailResponse(BaseModel):
    id: int
    role: str
    content: str
    sources: Optional[Any] = None
    created_at: datetime

    @field_validator("sources", mode="before")
    @classmethod
    def parse_sources(cls, v):
        """Helper validator to parse JSON string stored in DB to dict/list before returning."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return v
        return v

class ConversationDetailResponse(BaseModel):
    id: int
    title: str
    topic: str
    created_at: datetime
    messages: List[MessageDetailResponse]

class DeleteResponse(BaseModel):
    message: str


# --- Endpoints ---

@router.get("", response_model=List[ConversationSummaryResponse], status_code=status.HTTP_200_OK)
def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves the list of conversations for the current logged-in user.
    Ordered by updated_at descending.
    """
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    
    result = []
    for conv in conversations:
        result.append(
            ConversationSummaryResponse(
                id=conv.id,
                title=conv.title,
                topic=conv.topic,
                message_count=len(conv.messages),
                created_at=conv.created_at,
                updated_at=conv.updated_at
            )
        )
    return result


@router.get("/{conversation_id}", response_model=ConversationDetailResponse, status_code=status.HTTP_200_OK)
def get_conversation_detail(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves the detailed message history for a specific conversation.
    Verifies ownership and returns 404 if not found or unauthorized.
    """
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )
    
    # Verify existence and ownership
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy hội thoại"
        )
        
    messages_response = [
        MessageDetailResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            sources=msg.sources,
            created_at=msg.created_at
        )
        for msg in conversation.messages
    ]
    
    return ConversationDetailResponse(
        id=conversation.id,
        title=conversation.title,
        topic=conversation.topic,
        created_at=conversation.created_at,
        messages=messages_response
    )


@router.delete("/{conversation_id}", response_model=DeleteResponse, status_code=status.HTTP_200_OK)
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deletes a conversation and all its messages.
    Returns 403 if trying to delete another user's conversation.
    """
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy hội thoại"
        )
        
    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xóa hội thoại này"
        )
        
    db.delete(conversation)
    db.commit()
    
    return DeleteResponse(message="Đã xóa hội thoại thành công")
