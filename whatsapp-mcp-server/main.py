from typing import List, Dict, Any, Optional
from fastmcp import FastMCP
from whatsapp import (
    search_contacts as whatsapp_search_contacts,
    list_messages as whatsapp_list_messages,
    list_chats as whatsapp_list_chats,
    get_chat as whatsapp_get_chat,
    get_direct_chat_by_contact as whatsapp_get_direct_chat_by_contact,
    get_contact_chats as whatsapp_get_contact_chats,
    get_last_interaction as whatsapp_get_last_interaction,
    get_message_context as whatsapp_get_message_context,
    send_message as whatsapp_send_message,
    send_file as whatsapp_send_file,
    send_audio_message as whatsapp_audio_voice_message,
    download_media as whatsapp_download_media,
    login as whatsapp_login,
    get_qr_code as whatsapp_get_qr_code,
    get_login_status as whatsapp_get_login_status
)
import requests

# Initialize FastMCP server
mcp = FastMCP("whatsapp")

@mcp.tool()
def search_contacts(query: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Search WhatsApp contacts by name or phone number.
    
    Args:
        query: Search term to match against contact names or phone numbers
        user_id: Optional user ID to specify which database to use
    """
    contacts = whatsapp_search_contacts(query, user_id)
    return [contact.to_dict() for contact in contacts]

@mcp.tool()
def list_messages(
    user_id: str,
    after: Optional[str] = None,
    before: Optional[str] = None,
    sender_phone_number: Optional[str] = None,
    chat_jid: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 20,
    page: int = 0,
    include_context: bool = True,
    context_before: int = 1,
    context_after: int = 1
) -> List[Dict[str, Any]]:
    """Get WhatsApp messages matching specified criteria with optional context.
    
    Args:
        user_id: The user ID whose messages to list
        after: Optional ISO-8601 formatted string to only return messages after this date
        before: Optional ISO-8601 formatted string to only return messages before this date
        sender_phone_number: Optional phone number to filter messages by sender
        chat_jid: Optional chat JID to filter messages by chat
        query: Optional search term to filter messages by content
        limit: Maximum number of messages to return (default 20)
        page: Page number for pagination (default 0)
        include_context: Whether to include messages before and after matches (default True)
        context_before: Number of messages to include before each match (default 1)
        context_after: Number of messages to include after each match (default 1)
    """
    messages = whatsapp_list_messages(
        user_id=user_id,
        after=after,
        before=before,
        sender_phone_number=sender_phone_number,
        chat_jid=chat_jid,
        query=query,
        limit=limit,
        page=page,
        include_context=include_context,
        context_before=context_before,
        context_after=context_after
    )
    return [message.to_dict() for message in messages]

@mcp.tool()
def list_chats(
    user_id: str,
    query: Optional[str] = None,
    limit: int = 20,
    page: int = 0,
    include_last_message: bool = True,
    sort_by: str = "last_active"
) -> List[Dict[str, Any]]:
    """Get WhatsApp chats matching specified criteria for a specific user.
    
    Args:
        user_id: The user ID whose chats to list
        query: Optional search term to filter chats by name or JID
        limit: Maximum number of chats to return (default 20)
        page: Page number for pagination (default 0)
        include_last_message: Whether to include the last message in each chat (default True)
        sort_by: Field to sort results by, either "last_active" or "name" (default "last_active")
    """
    chats = whatsapp_list_chats(
        user_id=user_id,
        query=query,
        limit=limit,
        page=page,
        include_last_message=include_last_message,
        sort_by=sort_by
    )
    return [chat.to_dict() for chat in chats]

@mcp.tool()
def get_chat(user_id: str, chat_jid: str, include_last_message: bool = True) -> Dict[str, Any]:
    """Get WhatsApp chat metadata by JID for a specific user.
    
    Args:
        user_id: The user ID whose chat to get
        chat_jid: The JID of the chat to retrieve
        include_last_message: Whether to include the last message (default True)
    """
    chat = whatsapp_get_chat(user_id, chat_jid, include_last_message)
    return chat.to_dict() if chat else None

@mcp.tool()
def get_direct_chat_by_contact(user_id: str, sender_phone_number: str) -> Dict[str, Any]:
    """Get WhatsApp chat metadata by sender phone number for a specific user.
    
    Args:
        user_id: The user ID whose chat to get
        sender_phone_number: The phone number to search for
    """
    chat = whatsapp_get_direct_chat_by_contact(user_id, sender_phone_number)
    return chat.to_dict() if chat else None

@mcp.tool()
def get_contact_chats(user_id: str, jid: str, limit: int = 20, page: int = 0) -> List[Dict[str, Any]]:
    """Get all WhatsApp chats involving the contact for a specific user.
    
    Args:
        user_id: The user ID whose chats to get
        jid: The contact's JID to search for
        limit: Maximum number of chats to return (default 20)
        page: Page number for pagination (default 0)
    """
    chats = whatsapp_get_contact_chats(user_id, jid, limit, page)
    return [chat.to_dict() for chat in chats]

@mcp.tool()
def get_last_interaction(user_id: str, jid: str) -> str:
    """Get most recent WhatsApp message involving the contact for a specific user.
    
    Args:
        user_id: The user ID whose interaction to get
        jid: The JID of the contact to search for
    """
    message = whatsapp_get_last_interaction(user_id, jid)
    return message

@mcp.tool()
def get_message_context(
    message_id: str,
    before: int = 5,
    after: int = 5,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Get context around a specific WhatsApp message.
    
    Args:
        message_id: The ID of the message to get context for
        before: Number of messages to include before the target message (default 5)
        after: Number of messages to include after the target message (default 5)
        user_id: Optional user ID to specify which database to use
    """
    context = whatsapp_get_message_context(message_id, before, after, user_id)
    return context.to_dict() if context else None

@mcp.tool()
def send_message(
    recipient: str,
    message: str
) -> Dict[str, Any]:
    """Send a WhatsApp message to a person or group. For group chats use the JID.

    Args:
        recipient: The recipient - either a phone number with country code but no + or other symbols,
                 or a JID (e.g., "123456789@s.whatsapp.net" or a group JID like "123456789@g.us")
        message: The message text to send
    
    Returns:
        A dictionary containing success status and a status message
    """
    # Validate input
    if not recipient:
        return {
            "success": False,
            "message": "Recipient must be provided"
        }
    
    # Call the whatsapp_send_message function with the unified recipient parameter
    success, status_message = whatsapp_send_message(recipient, message)
    return {
        "success": success,
        "message": status_message
    }

@mcp.tool()
def send_file(recipient: str, media_path: str) -> Dict[str, Any]:
    """Send a file such as a picture, raw audio, video or document via WhatsApp to the specified recipient. For group messages use the JID.
    
    Args:
        recipient: The recipient - either a phone number with country code but no + or other symbols,
                 or a JID (e.g., "123456789@s.whatsapp.net" or a group JID like "123456789@g.us")
        media_path: The absolute path to the media file to send (image, video, document)
    
    Returns:
        A dictionary containing success status and a status message
    """
    
    # Call the whatsapp_send_file function
    success, status_message = whatsapp_send_file(recipient, media_path)
    return {
        "success": success,
        "message": status_message
    }

@mcp.tool()
def send_audio_message(recipient: str, media_path: str) -> Dict[str, Any]:
    """Send any audio file as a WhatsApp audio message to the specified recipient. For group messages use the JID. If it errors due to ffmpeg not being installed, use send_file instead.
    
    Args:
        recipient: The recipient - either a phone number with country code but no + or other symbols,
                 or a JID (e.g., "123456789@s.whatsapp.net" or a group JID like "123456789@g.us")
        media_path: The absolute path to the audio file to send (will be converted to Opus .ogg if it's not a .ogg file)
    
    Returns:
        A dictionary containing success status and a status message
    """
    success, status_message = whatsapp_audio_voice_message(recipient, media_path)
    return {
        "success": success,
        "message": status_message
    }

@mcp.tool()
def download_media(message_id: str, chat_jid: str) -> Dict[str, Any]:
    """Download media from a WhatsApp message and get the local file path or base64 data for images and PDFs.
    
    Args:
        message_id: The ID of the message containing the media
        chat_jid: The JID of the chat containing the message
    
    Returns:
        A dictionary containing success status, a status message, and either the file path or base64 data if successful
    """
    result = whatsapp_download_media(message_id, chat_jid)
    
    if result and isinstance(result, dict):
        # The result is already a dictionary object
        return result
    else:
        # Fallback for backward compatibility
        return {
            "success": False,
            "message": "Failed to download media"
        }

@mcp.tool()
def get_qr_code(user_id: Optional[str] = None) -> Dict[str, Any]:
    """DEPRECATED: Use the 'login' tool instead. This tool is kept for backward compatibility.
    
    Get QR code for WhatsApp login without polling for status.
    
    Args:
        user_id: Optional user ID. If not provided, will use or create a user ID automatically.
    
    Returns:
        A dictionary containing success status, QR code as base64, and status message
    """
    try:
        # Check if user is already logged in first
        status_result = whatsapp_get_login_status(user_id)
        if status_result["success"] and status_result["status"] == "success":
            return {
                "success": True,
                "user_id": status_result["user_id"],
                "message": "You are already logged in! No QR code needed. Use WhatsApp features directly.",
                "action_required": "none"
            }
        
        # Generate QR code if not logged in
        result = whatsapp_get_qr_code(user_id)
        if result["success"]:
            result["message"] = "DEPRECATED: Use the 'login' tool instead. " + result["message"]
        return result
    except Exception as e:
        return {
            "success": False,
            "message": f"QR code generation error: {str(e)}"
        }

@mcp.tool()
def login(user_id: Optional[str] = None) -> Dict[str, Any]:
    """Login to WhatsApp using QR code authentication.
    
    Args:
        user_id: Optional user ID. If not provided, will use or create a user ID automatically.
    
    Returns:
        A dictionary containing success status, QR code (if needed), and status message
    """
    try:
        # First check if user is already logged in
        status_result = whatsapp_get_login_status(user_id)
        
        if status_result["success"] and status_result["status"] == "success":
            # User is already logged in
            return {
                "success": True,
                "user_id": status_result["user_id"],
                "message": "You are already logged in! You can now use WhatsApp features.",
                "action_required": "none"
            }
        
        # User is not logged in, generate QR code
        qr_result = whatsapp_get_qr_code(user_id)
        if qr_result["success"]:
            return {
                "success": True,
                "qr_code_base64": qr_result["qr_code_base64"],
                "user_id": qr_result["user_id"],
                "message": "QR code generated. Please scan it with WhatsApp. Use get_login_status to check completion.",
                "action_required": "scan_qr_code"
            }
        else:
            return qr_result
    except Exception as e:
        return {
            "success": False,
            "message": f"Login error: {str(e)}"
        }

@mcp.tool()
def get_login_status(user_id: Optional[str] = None) -> Dict[str, Any]:
    """Check the login status for a specific user.
    
    Args:
        user_id: Optional user ID. If not provided, will use or create a user ID automatically.
    
    Returns:
        A dictionary containing login status and message
    """
    try:
        result = whatsapp_get_login_status(user_id)
        return result
    except Exception as e:
        return {
            "success": False,
            "status": "error",
            "message": f"Error checking login status: {str(e)}"
        }

if __name__ == "__main__":
    # Initialize and run the server with SSE transport
    import argparse
    
    parser = argparse.ArgumentParser(description='WhatsApp MCP Server')
    parser.add_argument('--transport', choices=['stdio', 'sse'], default='sse', 
                       help='Transport method (default: sse)')
    
    args = parser.parse_args()
    
    if args.transport == 'sse':
        print("Starting WhatsApp MCP Server with SSE transport")
        print("Note: SSE transport uses default FastMCP settings")
        mcp.run(transport='sse', host="0.0.0.0", port=8000)
        #mcp.run(transport='sse')
    else:
        print("Starting WhatsApp MCP Server with stdio transport")
        mcp.run(transport='stdio')
