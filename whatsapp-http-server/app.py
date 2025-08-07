from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from typing import Optional
from pydantic import BaseModel
from whatsapp import list_chats, Chat
from s3_service import s3_service

app = FastAPI()

# Add CORS middleware
origins = [
    "http://localhost:8080",
    "https://preview--know-chat-hive.lovable.app/"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/api/s3-file")
def get_s3_file(url: str = Query(..., description="S3 URL of the file to retrieve")):
    """
    Retrieve a file from S3 and return it as a response.
    Supports all file types including images, videos, documents, etc.
    """
    try:
        # Get file content from S3
        file_content, content_type, content_length = s3_service.get_file_from_s3(url)
        
        # Create response with appropriate headers
        response = Response(
            content=file_content,
            media_type=content_type,
            headers={
                "Content-Length": str(content_length),
                "Cache-Control": "public, max-age=3600",
                "Access-Control-Allow-Origin": "*"
            }
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test-s3")
def test_s3_url(url: str = Query(..., description="S3 URL to test")):
    """
    Test endpoint for debugging S3 URL parsing.
    """
    try:
        bucket, key = s3_service.extract_bucket_and_key_from_url(url)
        content_type = s3_service.get_content_type_from_extension(key)
        
        return {
            "original_url": url,
            "bucket": bucket,
            "key": key,
            "content_type": content_type
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 