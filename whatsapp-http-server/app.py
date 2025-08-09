from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from typing import Optional
from pydantic import BaseModel
import requests
import base64
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

# WhatsApp API base URL
WHATSAPP_API_BASE_URL = "http://localhost:8080/api"

class ChatModel(BaseModel):
    jid: str
    name: Optional[str]
    last_message_time: Optional[str]
    last_message: Optional[str] = None
    last_sender: Optional[str] = None
    last_is_from_me: Optional[bool] = None

class LoginRequest(BaseModel):
    user_id: str

class LoginResponse(BaseModel):
    success: bool
    user_id: str
    qr_code_base64: Optional[str] = None
    qr_code_path: Optional[str] = None
    message: str

class LoginStatusResponse(BaseModel):
    success: bool
    status: str
    user_id: str
    message: str

class ContactModel(BaseModel):
    jid: str
    name: str
    profile_image: Optional[str] = None
    is_group: bool

class ContactsResponse(BaseModel):
    success: bool
    user_id: str
    contacts: list[ContactModel]
    message: str

@app.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """
    Generate QR code for WhatsApp login.
    Returns base64 encoded QR code image.
    """
    try:
        user_id = request.user_id
        qr_url = f"{WHATSAPP_API_BASE_URL}/qr?user_id={user_id}"
        resp = requests.get(qr_url, timeout=10)
        
        if resp.status_code == 200:
            # Convert QR code image to base64
            qr_base64 = base64.b64encode(resp.content).decode('utf-8')
            
            # Also save to disk for backward compatibility
            qr_path = f"{user_id}_qr.png"
            with open(qr_path, "wb") as f:
                f.write(resp.content)
            
            return LoginResponse(
                success=True,
                user_id=user_id,
                qr_code_base64=qr_base64,
                qr_code_path=qr_path,
                message=f"QR code generated for user {user_id}. Please scan it with WhatsApp."
            )
        else:
            return LoginResponse(
                success=False,
                user_id=user_id,
                message=f"Failed to get QR code: {resp.text}"
            )
            
    except Exception as e:
        return LoginResponse(
            success=False,
            user_id=request.user_id,
            message=f"Error generating QR code: {str(e)}"
        )

@app.get("/login_status", response_model=LoginStatusResponse)
def get_login_status(user_id: str = Query(..., description="User ID to check login status for")):
    """
    Check the login status for a specific user.
    Returns login status: success, failed, pending, or unknown.
    """
    try:
        status_url = f"{WHATSAPP_API_BASE_URL}/login_status?user_id={user_id}"
        resp = requests.get(status_url, timeout=5)
        
        if resp.status_code == 200:
            status_data = resp.json()
            status = status_data.get("status", "unknown")
            
            if status == "success":
                return LoginStatusResponse(
                    success=True,
                    status="success",
                    user_id=user_id,
                    message="Login successful! You can now use WhatsApp features."
                )
            elif status == "failed":
                return LoginStatusResponse(
                    success=False,
                    status="failed",
                    user_id=user_id,
                    message="Login failed. Please try again."
                )
            elif status == "pending":
                return LoginStatusResponse(
                    success=False,
                    status="pending",
                    user_id=user_id,
                    message="Waiting for QR code scan. Please scan the QR code with WhatsApp."
                )
            else:
                return LoginStatusResponse(
                    success=False,
                    status="unknown",
                    user_id=user_id,
                    message=f"Unknown login status: {status}"
                )
        else:
            return LoginStatusResponse(
                success=False,
                status="error",
                user_id=user_id,
                message=f"Error checking login status: HTTP {resp.status_code}"
            )
            
    except Exception as e:
        return LoginStatusResponse(
            success=False,
            status="error",
            user_id=user_id,
            message=f"Error checking login status: {str(e)}"
        )

@app.get("/contacts", response_model=ContactsResponse)
def get_contacts(user_id: str = Query(..., description="User ID to fetch contacts for")):
    """
    Get all contacts and groups for a specific user.
    Returns list of contacts with their details.
    """
    try:
        url = f"{WHATSAPP_API_BASE_URL}/contacts?user_id={user_id}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            contacts_data = response.json()
            
            # Convert the raw contacts data to ContactModel objects
            contacts = []
            for contact in contacts_data:
                contacts.append(ContactModel(
                    jid=contact.get("jid", ""),
                    name=contact.get("name", ""),
                    profile_image=contact.get("profile_image"),
                    is_group=contact.get("is_group", False)
                ))
            
            return ContactsResponse(
                success=True,
                user_id=user_id,
                contacts=contacts,
                message=f"Contacts and joined groups for user {user_id}."
            )
        else:
            return ContactsResponse(
                success=False,
                user_id=user_id,
                contacts=[],
                message=f"Failed to get contacts: HTTP {response.status_code} - {response.text}"
            )
            
    except requests.exceptions.RequestException as e:
        return ContactsResponse(
            success=False,
            user_id=user_id,
            contacts=[],
            message=f"Network error while fetching contacts: {str(e)}"
        )
    except Exception as e:
        return ContactsResponse(
            success=False,
            user_id=user_id,
            contacts=[],
            message=f"Error getting contacts: {str(e)}"
        )

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