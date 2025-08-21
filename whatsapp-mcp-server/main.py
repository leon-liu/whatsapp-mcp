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
    get_login_status as whatsapp_get_login_status,
    get_contacts as whatsapp_get_contacts
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
def download_media(message_id: str, chat_jid: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """Download media from a WhatsApp message and get the local file path or S3 URL.
    
    Args:
        message_id: The ID of the message containing the media
        chat_jid: The JID of the chat containing the message
        user_id: Optional user ID. If not provided, will use or create a user ID automatically.
    
    Returns:
        A dictionary containing success status, a status message, and either the file path or S3 URL if successful
    """
    result = whatsapp_download_media(user_id, message_id, chat_jid)
    
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

# @mcp.tool()
# def get_contacts(user_id: Optional[str] = None) -> Dict[str, Any]:
#     """Get all WhatsApp contacts for a specific user.
    
#     Args:
#         user_id: Optional user ID. If not provided, will use or create a user ID automatically.
    
#     Returns:
#         A dictionary containing success status, contacts list, and status message
#     """
#     try:
#         result = whatsapp_get_contacts(user_id)
#         return result
#     except Exception as e:
#         return {
#             "success": False,
#             "status": "error",
#             "message": f"Error getting contacts: {str(e)}"
#         }

@mcp.tool()
def filter_messages_by_keywords(
    user_id: str,
    keywords: List[str],
    chat_jid: Optional[str] = None,
    after: Optional[str] = None,
    before: Optional[str] = None,
    sender_phone_number: Optional[str] = None,
    case_sensitive: bool = False,
    include_context: bool = True,
    context_before: int = 2,
    context_after: int = 2,
    limit: int = 50,
    page: int = 0
) -> Dict[str, Any]:
    """Filter WhatsApp messages based on keywords with optional context and filtering.
    
    Args:
        user_id: The user ID whose messages to filter
        keywords: List of keywords to search for in message content
        chat_jid: Optional chat JID to filter messages by specific chat
        after: Optional ISO-8601 formatted string to only return messages after this date
        before: Optional ISO-8601 formatted string to only return messages before this date
        sender_phone_number: Optional phone number to filter messages by sender
        case_sensitive: Whether keyword matching should be case sensitive (default False)
        include_context: Whether to include messages before and after matches (default True)
        context_before: Number of messages to include before each match (default 2)
        context_after: Number of messages to include after each match (default 2)
        limit: Maximum number of keyword matches to return (default 50)
        page: Page number for pagination (default 0)
    
    Returns:
        A dictionary containing:
        - success: Boolean indicating if the operation was successful
        - filtered_messages: List of messages containing keywords with context
        - total_matches: Total number of keyword matches found
        - keywords_used: List of keywords that were searched for
        - filters_applied: Summary of filters applied
        - message: Status message
    """
    try:
        # First get all messages with basic filtering
        all_messages = whatsapp_list_messages(
            user_id=user_id,
            after=after,
            before=before,
            sender_phone_number=sender_phone_number,
            chat_jid=chat_jid,
            query=None,  # We'll do keyword filtering manually
            limit=1000,  # Get more messages for keyword filtering
            page=0,
            include_context=False,  # We'll add context after filtering
            context_before=0,
            context_after=0
        )
        
        if not all_messages:
            return {
                "success": True,
                "filtered_messages": [],
                "total_matches": 0,
                "keywords_used": keywords,
                "filters_applied": {
                    "chat_jid": chat_jid,
                    "after": after,
                    "before": before,
                    "sender_phone_number": sender_phone_number,
                    "case_sensitive": case_sensitive
                },
                "message": "No messages found matching the criteria"
            }
        
        # Filter messages by keywords
        keyword_matches = []
        for message in all_messages:
            message_content = message.content.lower() if not case_sensitive else message.content
            
            # Check if any keyword matches
            matched_keywords = []
            for keyword in keywords:
                keyword_lower = keyword.lower() if not case_sensitive else keyword
                if keyword_lower in message_content:
                    matched_keywords.append(keyword)
            
            if matched_keywords:
                # Add matched keywords to message data
                message_dict = message.to_dict()
                message_dict['matched_keywords'] = matched_keywords
                keyword_matches.append(message_dict)
        
        # Sort by timestamp (newest first)
        keyword_matches.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Apply pagination
        start_idx = page * limit
        end_idx = start_idx + limit
        paginated_matches = keyword_matches[start_idx:end_idx]
        
        # Add context if requested
        if include_context and paginated_matches:
            messages_with_context = []
            for match in paginated_matches:
                # Get context for each matched message
                context = whatsapp_get_message_context(
                    match['id'], 
                    context_before, 
                    context_after, 
                    user_id
                )
                
                if context:
                    # Add context messages
                    context_messages = []
                    for ctx_msg in context.before:
                        ctx_dict = ctx_msg.to_dict()
                        ctx_dict['context_type'] = 'before'
                        context_messages.append(ctx_dict)
                    
                    # Add the matched message
                    match['context_type'] = 'match'
                    context_messages.append(match)
                    
                    for ctx_msg in context.after:
                        ctx_dict = ctx_msg.to_dict()
                        ctx_dict['context_type'] = 'after'
                        context_messages.append(ctx_dict)
                    
                    messages_with_context.extend(context_messages)
                else:
                    messages_with_context.append(match)
            
            paginated_matches = messages_with_context
        
        return {
            "success": True,
            "filtered_messages": paginated_matches,
            "total_matches": len(keyword_matches),
            "keywords_used": keywords,
            "filters_applied": {
                "chat_jid": chat_jid,
                "after": after,
                "before": before,
                "sender_phone_number": sender_phone_number,
                "case_sensitive": case_sensitive,
                "include_context": include_context,
                "context_before": context_before,
                "context_after": context_after
            },
            "message": f"Found {len(keyword_matches)} messages containing keywords: {', '.join(keywords)}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "filtered_messages": [],
            "total_matches": 0,
            "keywords_used": keywords,
            "filters_applied": {},
            "message": f"Error filtering messages by keywords: {str(e)}"
        }

@mcp.tool()
def filter_messages_by_keywords_in_chats(
    user_id: str,
    keywords: List[str],
    chat_jids: List[str],
    after: Optional[str] = None,
    before: Optional[str] = None,
    sender_phone_number: Optional[str] = None,
    case_sensitive: bool = False,
    include_context: bool = False,
    context_before: int = 1,
    context_after: int = 1,
    limit: int = 100,
    page: int = 0,
    return_original_only: bool = True
) -> Dict[str, Any]:
    """Filter WhatsApp messages by keywords from specific chat JIDs and return original messages.
    
    Args:
        user_id: The user ID whose messages to filter
        keywords: List of keywords to search for in message content
        chat_jids: List of specific chat JIDs to search in (e.g., ["123@g.us", "456@s.whatsapp.net"])
        after: Optional ISO-8601 formatted string to only return messages after this date
        before: Optional ISO-8601 formatted string to only return messages before this date
        sender_phone_number: Optional phone number to filter messages by sender
        case_sensitive: Whether keyword matching should be case sensitive (default False)
        include_context: Whether to include messages before and after matches (default False)
        context_before: Number of messages to include before each match (default 1)
        context_after: Number of messages to include after each match (default 1)
        limit: Maximum number of keyword matches to return (default 100)
        page: Page number for pagination (default 0)
        return_original_only: If True, only return messages with keywords; if False, include context (default True)
    
    Returns:
        A dictionary containing:
        - success: Boolean indicating if the operation was successful
        - filtered_messages: List of original messages containing keywords (with optional context)
        - total_matches: Total number of keyword matches found across all specified chats
        - keywords_used: List of keywords that were searched for
        - chat_jids_searched: List of chat JIDs that were searched
        - matches_per_chat: Breakdown of matches found in each chat
        - filters_applied: Summary of filters applied
        - message: Status message
    """
    try:
        if not chat_jids:
            return {
                "success": False,
                "filtered_messages": [],
                "total_matches": 0,
                "keywords_used": keywords,
                "chat_jids_searched": [],
                "matches_per_chat": {},
                "filters_applied": {},
                "message": "No chat JIDs provided for filtering"
            }
        
        # Collect messages from all specified chats
        all_messages = []
        matches_per_chat = {}
        
        for chat_jid in chat_jids:
            # Get messages for this specific chat
            chat_messages = whatsapp_list_messages(
                user_id=user_id,
                after=after,
                before=before,
                sender_phone_number=sender_phone_number,
                chat_jid=chat_jid,
                query=None,  # We'll do keyword filtering manually
                limit=1000,  # Get more messages for keyword filtering
                page=0,
                include_context=False,
                context_before=0,
                context_after=0
            )
            
            if chat_messages:
                all_messages.extend(chat_messages)
                matches_per_chat[chat_jid] = 0  # Initialize counter
        
        if not all_messages:
            return {
                "success": True,
                "filtered_messages": [],
                "total_matches": 0,
                "keywords_used": keywords,
                "chat_jids_searched": chat_jids,
                "matches_per_chat": matches_per_chat,
                "filters_applied": {
                    "chat_jids": chat_jids,
                    "after": after,
                    "before": before,
                    "sender_phone_number": sender_phone_number,
                    "case_sensitive": case_sensitive,
                    "include_context": include_context
                },
                "message": f"No messages found in the specified {len(chat_jids)} chat(s)"
            }
        
        # Filter messages by keywords
        keyword_matches = []
        for message in all_messages:
            message_content = message.content.lower() if not case_sensitive else message.content
            
            # Check if any keyword matches
            matched_keywords = []
            for keyword in keywords:
                keyword_lower = keyword.lower() if not case_sensitive else keyword
                if keyword_lower in message_content:
                    matched_keywords.append(keyword)
            
            if matched_keywords:
                # Add matched keywords and chat info to message data
                message_dict = message.to_dict()
                message_dict['matched_keywords'] = matched_keywords
                message_dict['chat_jid'] = message.chat_jid
                message_dict['chat_name'] = message.chat_name
                
                keyword_matches.append(message_dict)
                
                # Update matches counter for this chat
                if message.chat_jid in matches_per_chat:
                    matches_per_chat[message.chat_jid] += 1
        
        # Sort by timestamp (newest first)
        keyword_matches.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Apply pagination
        start_idx = page * limit
        end_idx = start_idx + limit
        paginated_matches = keyword_matches[start_idx:end_idx]
        
        # Add context if requested and not returning original only
        if include_context and not return_original_only and paginated_matches:
            messages_with_context = []
            for match in paginated_matches:
                # Get context for each matched message
                context = whatsapp_get_message_context(
                    match['id'], 
                    context_before, 
                    context_after, 
                    user_id
                )
                
                if context:
                    # Add context messages
                    context_messages = []
                    for ctx_msg in context.before:
                        ctx_dict = ctx_msg.to_dict()
                        ctx_dict['context_type'] = 'before'
                        ctx_dict['chat_jid'] = ctx_msg.chat_jid
                        ctx_dict['chat_name'] = ctx_msg.chat_name
                        context_messages.append(ctx_dict)
                    
                    # Add the matched message
                    match['context_type'] = 'match'
                    context_messages.append(match)
                    
                    for ctx_msg in context.after:
                        ctx_dict = ctx_msg.to_dict()
                        ctx_dict['context_type'] = 'after'
                        ctx_dict['chat_jid'] = ctx_msg.chat_jid
                        ctx_dict['chat_name'] = ctx_msg.chat_name
                        context_messages.append(ctx_dict)
                    
                    messages_with_context.extend(context_messages)
                else:
                    messages_with_context.append(match)
            
            paginated_matches = messages_with_context
        
        return {
            "success": True,
            "filtered_messages": paginated_matches,
            "total_matches": len(keyword_matches),
            "keywords_used": keywords,
            "chat_jids_searched": chat_jids,
            "matches_per_chat": matches_per_chat,
            "filters_applied": {
                "chat_jids": chat_jids,
                "after": after,
                "before": before,
                "sender_phone_number": sender_phone_number,
                "case_sensitive": case_sensitive,
                "include_context": include_context,
                "context_before": context_before,
                "context_after": context_after,
                "return_original_only": return_original_only
            },
            "message": f"Found {len(keyword_matches)} messages containing keywords '{', '.join(keywords)}' across {len(chat_jids)} chat(s)"
        }
        
    except Exception as e:
        return {
            "success": False,
            "filtered_messages": [],
            "total_matches": 0,
            "keywords_used": keywords,
            "chat_jids_searched": chat_jids if 'chat_jids' in locals() else [],
            "matches_per_chat": {},
            "filters_applied": {},
            "message": f"Error filtering messages by keywords in chats: {str(e)}"
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
