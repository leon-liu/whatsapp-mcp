from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from typing import Optional
from pydantic import BaseModel
import requests
import base64
from whatsapp import list_chats, Chat, get_allowed_contacts
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
    media_type: Optional[str] = None
    message_id: Optional[str] = None
    message_timestamp: Optional[str] = None

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

class AllowContactRequest(BaseModel):
    jid: str
    name: str

class AllowContactsRequest(BaseModel):
    user_id: str
    contacts: list[AllowContactRequest]

class AllowContactsResponse(BaseModel):
    success: bool
    message: str
    allowed: int

class AllowedContactModel(BaseModel):
    jid: str
    name: Optional[str]
    last_message_time: Optional[str]
    is_allowed: bool
    is_group: bool

class AllowedContactsResponse(BaseModel):
    success: bool
    user_id: str
    allowed_contacts: list[AllowedContactModel]
    count: int
    message: str

class DownloadMediaRequest(BaseModel):
    message_id: str
    chat_jid: str

class DownloadMediaResponse(BaseModel):
    success: bool
    message: str
    filename: Optional[str] = None
    path: Optional[str] = None
    s3_url: Optional[str] = None

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

@app.post("/allow_contacts", response_model=AllowContactsResponse)
def allow_contacts(request: AllowContactsRequest):
    """
    Allow specific contacts to send messages.
    Updates the is_allowed status for the specified contacts.
    """
    try:
        url = f"{WHATSAPP_API_BASE_URL}/allow_contacts"
        response = requests.post(url, json={
            "user_id": request.user_id,
            "contacts": [{"jid": contact.jid, "name": contact.name} for contact in request.contacts]
        }, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return AllowContactsResponse(
                success=result.get("success", False),
                message=result.get("message", ""),
                allowed=result.get("allowed", 0)
            )
        else:
            return AllowContactsResponse(
                success=False,
                message=f"Failed to allow contacts: HTTP {response.status_code} - {response.text}",
                allowed=0
            )
            
    except requests.exceptions.RequestException as e:
        return AllowContactsResponse(
            success=False,
            message=f"Network error while allowing contacts: {str(e)}",
            allowed=0
        )
    except Exception as e:
        return AllowContactsResponse(
            success=False,
            message=f"Error allowing contacts: {str(e)}",
            allowed=0
        )

@app.get("/allow_contacts", response_model=AllowedContactsResponse)
def get_allowed_contacts_endpoint(user_id: str = Query(..., description="User ID to fetch allowed contacts for")):
    """
    Get all allowed contacts for a specific user by reading directly from the database.
    Returns list of contacts that have is_allowed = TRUE.
    """
    try:
        result = get_allowed_contacts(user_id=user_id)
        return AllowedContactsResponse(
            success=result.get("success", False),
            user_id=result.get("user_id", user_id),
            allowed_contacts=result.get("allowed_contacts", []),
            count=result.get("count", 0),
            message=result.get("message", "")
        )
    except Exception as e:
        return AllowedContactsResponse(
            success=False,
            user_id=user_id,
            allowed_contacts=[],
            count=0,
            message=f"Error getting allowed contacts: {str(e)}"
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

@app.post("/download", response_model=DownloadMediaResponse)
def download_media(
    request: DownloadMediaRequest,
    user_id: str = Query(..., description="User ID to download media for")
):
    """
    Download media from a WhatsApp message by calling the WhatsApp bridge API.
    Returns download status and file information.
    """
    try:
        # Call the WhatsApp bridge download endpoint
        url = f"{WHATSAPP_API_BASE_URL}/download?user_id={user_id}"
        
        response = requests.post(url, json=request.dict())
        response.raise_for_status()
        
        # Parse the response from WhatsApp bridge
        bridge_response = response.json()
        
        return DownloadMediaResponse(
            success=bridge_response.get("success", False),
            message=bridge_response.get("message", ""),
            filename=bridge_response.get("filename"),
            path=bridge_response.get("path"),
            s3_url=bridge_response.get("s3_url")
        )
        
    except requests.exceptions.RequestException as e:
        return DownloadMediaResponse(
            success=False,
            message=f"Network error while downloading media: {str(e)}"
        )
    except Exception as e:
        return DownloadMediaResponse(
            success=False,
            message=f"Error downloading media: {str(e)}"
        )

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