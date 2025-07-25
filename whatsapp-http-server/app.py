from fastapi import FastAPI, Query, HTTPException
from typing import Optional
from pydantic import BaseModel
from whatsapp import list_chats, Chat

app = FastAPI()

class ChatModel(BaseModel):
    jid: str
    name: Optional[str]
    last_message_time: Optional[str]
    last_message: Optional[str] = None
    last_sender: Optional[str] = None
    last_is_from_me: Optional[bool] = None

@app.get("/chats", response_model=list[ChatModel])
def get_chats(
    user_id: str = Query(..., description="User ID to fetch chats for"),
    query: Optional[str] = Query(None),
    limit: int = Query(20),
    page: int = Query(0),
    include_last_message: bool = Query(True),
    sort_by: str = Query("last_active")
):
    try:
        chats = list_chats(
            user_id=user_id,
            query=query,
            limit=limit,
            page=page,
            include_last_message=include_last_message,
            sort_by=sort_by
        )
        return [chat.to_dict() for chat in chats]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 