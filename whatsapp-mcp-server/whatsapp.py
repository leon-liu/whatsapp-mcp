import sqlite3
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict, Any
import os.path
import requests
import json
import audio
import uuid
import os
import time
import base64

MESSAGES_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'whatsapp-bridge', 'store', 'messages.db')
WHATSAPP_API_BASE_URL = "http://localhost:8080/api"
USER_ID_FILE = "user_id.txt"

def get_or_create_user_id():
    if os.path.exists(USER_ID_FILE):
        with open(USER_ID_FILE, "r") as f:
            return f.read().strip()
    user_id = str(uuid.uuid4())
    with open(USER_ID_FILE, "w") as f:
        f.write(user_id)
    return user_id

user_id = get_or_create_user_id()

@dataclass
class Message:
    timestamp: datetime
    sender: str
    content: str
    is_from_me: bool
    chat_jid: str
    id: str
    chat_name: Optional[str] = None
    media_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'sender': self.sender,
            'content': self.content,
            'is_from_me': self.is_from_me,
            'chat_jid': self.chat_jid,
            'id': self.id,
            'chat_name': self.chat_name,
            'media_type': self.media_type
        }

@dataclass
class Chat:
    jid: str
    name: Optional[str]
    last_message_time: Optional[datetime]
    last_message: Optional[str] = None
    last_sender: Optional[str] = None
    last_sender_name: Optional[str] = None
    last_is_from_me: Optional[bool] = None

    @property
    def is_group(self) -> bool:
        """Determine if chat is a group based on JID pattern."""
        return self.jid.endswith("@g.us")

    def to_dict(self) -> Dict[str, Any]:
        return {
            'jid': self.jid,
            'name': self.name,
            'last_message_time': self.last_message_time.isoformat() if self.last_message_time else None,
            'last_message': self.last_message,
            'last_sender': self.last_sender,
            'last_sender_name': self.last_sender_name,
            'last_is_from_me': self.last_is_from_me,
            'is_group': self.is_group
        }

@dataclass
class Contact:
    phone_number: str
    name: Optional[str]
    jid: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'phone_number': self.phone_number,
            'name': self.name,
            'jid': self.jid
        }

@dataclass
class MessageContext:
    message: Message
    before: List[Message]
    after: List[Message]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'message': self.message.to_dict(),
            'before': [msg.to_dict() for msg in self.before],
            'after': [msg.to_dict() for msg in self.after]
        }

def git(sender_jid: str, user_id: Optional[str] = None) -> str:
    try:
        if user_id:
            db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../whatsapp-bridge/store", user_id, "messages.db"))
        else:
            db_path = MESSAGES_DB_PATH
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # First try matching by exact JID
        cursor.execute("""
            SELECT name
            FROM chats
            WHERE jid = ?
            LIMIT 1
        """, (sender_jid,))
        
        result = cursor.fetchone()
        
        # If no result, try looking for the number within JIDs
        if not result:
            # Extract the phone number part if it's a JID
            if '@' in sender_jid:
                phone_part = sender_jid.split('@')[0]
            else:
                phone_part = sender_jid
                
            cursor.execute("""
                SELECT name
                FROM chats
                WHERE jid LIKE ?
                LIMIT 1
            """, (f"%{phone_part}%",))
            
            result = cursor.fetchone()
        
        if result and result[0]:
            return result[0]
        else:
            return sender_jid
        
    except sqlite3.Error as e:
        print(f"Database error while getting sender name: {e}")
        return sender_jid
    finally:
        if 'conn' in locals():
            conn.close()

def format_message(message: Message, show_chat_info: bool = True, user_id: Optional[str] = None) -> str:
    """Print a single message with consistent formatting."""
    output = ""
    
    if show_chat_info and message.chat_name:
        output += f"[{message.timestamp:%Y-%m-%d %H:%M:%S}] Chat: {message.chat_name} "
    else:
        output += f"[{message.timestamp:%Y-%m-%d %H:%M:%S}] "
        
    content_prefix = ""
    if hasattr(message, 'media_type') and message.media_type:
        content_prefix = f"[{message.media_type} - Message ID: {message.id} - Chat JID: {message.chat_jid}] "
    
    try:
        sender_name = git(message.sender, user_id) if not message.is_from_me else "Me"
        output += f"From: {sender_name}: {content_prefix}{message.content}\n"
    except Exception as e:
        print(f"Error formatting message: {e}")
    return output

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
) -> List[Message]:
    """Get messages matching the specified criteria with optional context."""
    try:
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../whatsapp-bridge/store", user_id, "messages.db"))
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Build base query
        query_parts = ["SELECT messages.timestamp, messages.sender, chats.name, messages.content, messages.is_from_me, chats.jid, messages.id, messages.media_type FROM messages"]
        query_parts.append("JOIN chats ON messages.chat_jid = chats.jid")
        where_clauses = []
        params = []
        
        # Add filters
        if after:
            try:
                after = datetime.fromisoformat(after)
            except ValueError:
                raise ValueError(f"Invalid date format for 'after': {after}. Please use ISO-8601 format.")
            
            where_clauses.append("messages.timestamp > ?")
            params.append(after)

        if before:
            try:
                before = datetime.fromisoformat(before)
            except ValueError:
                raise ValueError(f"Invalid date format for 'before': {before}. Please use ISO-8601 format.")
            
            where_clauses.append("messages.timestamp < ?")
            params.append(before)

        if sender_phone_number:
            where_clauses.append("messages.sender = ?")
            params.append(sender_phone_number)
        
        if chat_jid:
            # Ensure chat_jid has the proper suffix
            if not chat_jid.endswith("@s.whatsapp.net") and not chat_jid.endswith("@g.us"):
                chat_jid = chat_jid + "@s.whatsapp.net"
            where_clauses.append("messages.chat_jid = ?")
            params.append(chat_jid)
            
        if query:
            where_clauses.append("LOWER(messages.content) LIKE LOWER(?)")
            params.append(f"%{query}%")
            
        # Always filter by allowed contacts and only groups (JID ending with @g.us)
        where_clauses.append("chats.is_allowed = TRUE AND chats.jid LIKE '%@g.us'")
            
        if where_clauses:
            query_parts.append("WHERE " + " AND ".join(where_clauses))
            
        # Add pagination
        offset = page * limit
        query_parts.append("ORDER BY messages.timestamp DESC")
        query_parts.append("LIMIT ? OFFSET ?")
        params.extend([limit, offset])
        
        cursor.execute(" ".join(query_parts), tuple(params))
        messages = cursor.fetchall()
        
        result = []
        for msg in messages:
            message = Message(
                timestamp=datetime.fromisoformat(msg[0]),
                sender=msg[1],
                chat_name=msg[2],
                content=msg[3],
                is_from_me=msg[4],
                chat_jid=msg[5],
                id=msg[6],
                media_type=msg[7]
            )
            result.append(message)
            
        if include_context and result:
            # Add context for each message
            messages_with_context = []
            for msg in result:
                context = get_message_context(msg.id, context_before, context_after, user_id)
                messages_with_context.extend(context.before)
                messages_with_context.append(context.message)
                messages_with_context.extend(context.after)
            
            return messages_with_context
        
        # Return messages without context
        return result
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


def get_message_context(
    message_id: str,
    before: int = 5,
    after: int = 5,
    user_id: Optional[str] = None
) -> MessageContext:
    """Get context around a specific message."""
    try:
        if user_id:
            db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../whatsapp-bridge/store", user_id, "messages.db"))
        else:
            db_path = MESSAGES_DB_PATH
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get the target message first
        cursor.execute("""
            SELECT messages.timestamp, messages.sender, chats.name, messages.content, messages.is_from_me, chats.jid, messages.id, messages.chat_jid, messages.media_type
            FROM messages
            JOIN chats ON messages.chat_jid = chats.jid
            WHERE messages.id = ?
        """, (message_id,))
        msg_data = cursor.fetchone()
        
        if not msg_data:
            raise ValueError(f"Message with ID {message_id} not found")
            
        target_message = Message(
            timestamp=datetime.fromisoformat(msg_data[0]),
            sender=msg_data[1],
            chat_name=msg_data[2],
            content=msg_data[3],
            is_from_me=msg_data[4],
            chat_jid=msg_data[5],
            id=msg_data[6],
            media_type=msg_data[8]
        )
        
        # Get messages before
        cursor.execute("""
            SELECT messages.timestamp, messages.sender, chats.name, messages.content, messages.is_from_me, chats.jid, messages.id, messages.media_type
            FROM messages
            JOIN chats ON messages.chat_jid = chats.jid
            WHERE messages.chat_jid = ? AND messages.timestamp < ?
            ORDER BY messages.timestamp DESC
            LIMIT ?
        """, (msg_data[7], msg_data[0], before))
        
        before_messages = []
        for msg in cursor.fetchall():
            before_messages.append(Message(
                timestamp=datetime.fromisoformat(msg[0]),
                sender=msg[1],
                chat_name=msg[2],
                content=msg[3],
                is_from_me=msg[4],
                chat_jid=msg[5],
                id=msg[6],
                media_type=msg[7]
            ))
        
        # Get messages after
        cursor.execute("""
            SELECT messages.timestamp, messages.sender, chats.name, messages.content, messages.is_from_me, chats.jid, messages.id, messages.media_type
            FROM messages
            JOIN chats ON messages.chat_jid = chats.jid
            WHERE messages.chat_jid = ? AND messages.timestamp > ?
            ORDER BY messages.timestamp ASC
            LIMIT ?
        """, (msg_data[7], msg_data[0], after))
        
        after_messages = []
        for msg in cursor.fetchall():
            after_messages.append(Message(
                timestamp=datetime.fromisoformat(msg[0]),
                sender=msg[1],
                chat_name=msg[2],
                content=msg[3],
                is_from_me=msg[4],
                chat_jid=msg[5],
                id=msg[6],
                media_type=msg[7]
            ))
        
        return MessageContext(
            message=target_message,
            before=before_messages,
            after=after_messages
        )
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()


def list_chats(user_id: str,
    query: Optional[str] = None,
    limit: int = 20,
    page: int = 0,
    include_last_message: bool = True,
    sort_by: str = "last_active"
) -> List[Chat]:
    """Get group chats matching the specified criteria (only JIDs ending with @g.us)."""
    try:
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../whatsapp-bridge/store", user_id, "messages.db"))
        print("DB path:", db_path)
        print("CWD:", os.getcwd())
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Build base query
        query_parts = ["""
            SELECT 
                chats.jid,
                chats.name,
                chats.last_message_time,
                messages.content as last_message,
                messages.sender as last_sender,
                messages.is_from_me as last_is_from_me,
                sender_chat.name as last_sender_name
            FROM chats
        """]
        
        if include_last_message:
            query_parts.append("""
                LEFT JOIN messages ON chats.jid = messages.chat_jid 
                AND chats.last_message_time = messages.timestamp
                LEFT JOIN chats sender_chat ON messages.sender = sender_chat.jid
            """)
            
        where_clauses = []
        params = []
        
        if query:
            where_clauses.append("(LOWER(chats.name) LIKE LOWER(?) OR chats.jid LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])
            
        # Always filter by allowed contacts and only groups (JID ending with @g.us)
        where_clauses.append("chats.is_allowed = TRUE AND chats.jid LIKE '%@g.us'")
            
        if where_clauses:
            query_parts.append("WHERE " + " AND ".join(where_clauses))
            
        # Add sorting
        order_by = "chats.last_message_time DESC" if sort_by == "last_active" else "chats.name"
        query_parts.append(f"ORDER BY {order_by}")
        
        # Add pagination
        offset = (page ) * limit
        query_parts.append("LIMIT ? OFFSET ?")
        params.extend([limit, offset])
        
        cursor.execute(" ".join(query_parts), tuple(params))
        chats = cursor.fetchall()
        
        result = []
        for chat_data in chats:
            chat = Chat(
                jid=chat_data[0],
                name=chat_data[1],
                last_message_time=datetime.fromisoformat(chat_data[2]) if chat_data[2] else None,
                last_message=chat_data[3],
                last_sender=chat_data[4],
                last_sender_name=chat_data[6],
                last_is_from_me=chat_data[5]
            )
            result.append(chat)
            
        return result
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


def search_contacts(query: str, user_id: Optional[str] = None) -> List[Contact]:
    """Search contacts by name or phone number."""
    try:
        if user_id:
            db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../whatsapp-bridge/store", user_id, "messages.db"))
        else:
            db_path = MESSAGES_DB_PATH
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Split query into characters to support partial matching
        search_pattern = '%' +query + '%'
        
        cursor.execute("""
            SELECT DISTINCT 
                jid,
                name
            FROM chats
            WHERE 
                (LOWER(name) LIKE LOWER(?) OR LOWER(jid) LIKE LOWER(?))
                AND jid NOT LIKE '%@g.us'
            ORDER BY name, jid
            LIMIT 50
        """, (search_pattern, search_pattern))
        
        contacts = cursor.fetchall()
        
        result = []
        for contact_data in contacts:
            contact = Contact(
                phone_number=contact_data[0].split('@')[0],
                name=contact_data[1],
                jid=contact_data[0]
            )
            result.append(contact)
            
        return result
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


def get_contact_chats(user_id: str, jid: str, limit: int = 20, page: int = 0) -> List[Chat]:
    """Get all group chats involving the contact (only JIDs ending with @g.us).
    
    Args:
        jid: The contact's JID to search for
        limit: Maximum number of chats to return (default 20)
        page: Page number for pagination (default 0)
    """
    try:
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../whatsapp-bridge/store", user_id, "messages.db"))
        print("DB path:", db_path)
        print("CWD:", os.getcwd())
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT
                c.jid,
                c.name,
                c.last_message_time,
                m.content as last_message,
                m.sender as last_sender,
                m.is_from_me as last_is_from_me
            FROM chats c
            JOIN messages m ON c.jid = m.chat_jid
            WHERE (m.sender = ? OR c.jid = ?) AND c.jid LIKE '%@g.us'
            ORDER BY c.last_message_time DESC
            LIMIT ? OFFSET ?
        """, (jid, jid, limit, page * limit))
        
        chats = cursor.fetchall()
        
        result = []
        for chat_data in chats:
            chat = Chat(
                jid=chat_data[0],
                name=chat_data[1],
                last_message_time=datetime.fromisoformat(chat_data[2]) if chat_data[2] else None,
                last_message=chat_data[3],
                last_sender=chat_data[4],
                last_sender_name=None,  # This function doesn't include sender name
                last_is_from_me=chat_data[5]
            )
            result.append(chat)
            
        return result
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


def get_last_interaction(user_id: str, jid: str) -> str:
    """Get most recent message involving the group contact (only JIDs ending with @g.us)."""
    try:
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../whatsapp-bridge/store", user_id, "messages.db"))
        print("DB path:", db_path)
        print("CWD:", os.getcwd())
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                m.timestamp,
                m.sender,
                c.name,
                m.content,
                m.is_from_me,
                c.jid,
                m.id,
                m.media_type
            FROM messages m
            JOIN chats c ON m.chat_jid = c.jid
            WHERE (m.sender = ? OR c.jid = ?) AND c.jid LIKE '%@g.us'
            ORDER BY m.timestamp DESC
            LIMIT 1
        """, (jid, jid))
        
        msg_data = cursor.fetchone()
        
        if not msg_data:
            return None
            
        message = Message(
            timestamp=datetime.fromisoformat(msg_data[0]),
            sender=msg_data[1],
            chat_name=msg_data[2],
            content=msg_data[3],
            is_from_me=msg_data[4],
            chat_jid=msg_data[5],
            id=msg_data[6],
            media_type=msg_data[7]
        )
        
        return format_message(message)
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()


def get_chat(user_id: str, chat_jid: str, include_last_message: bool = True) -> Optional[Chat]:
    """Get chat metadata by JID."""
    try:
        # Ensure chat_jid has the proper suffix
        if not chat_jid.endswith("@s.whatsapp.net") and not chat_jid.endswith("@g.us"):
            chat_jid = chat_jid + "@s.whatsapp.net"
            
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../whatsapp-bridge/store", user_id, "messages.db"))
        print("DB path:", db_path)
        print("CWD:", os.getcwd())
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT 
                c.jid,
                c.name,
                c.last_message_time,
                m.content as last_message,
                m.sender as last_sender,
                m.is_from_me as last_is_from_me
            FROM chats c
        """
        
        if include_last_message:
            query += """
                LEFT JOIN messages m ON c.jid = m.chat_jid 
                AND c.last_message_time = m.timestamp
            """
            
        query += " WHERE c.jid = ?"
        
        cursor.execute(query, (chat_jid,))
        chat_data = cursor.fetchone()
        
        if not chat_data:
            return None
            
        return Chat(
            jid=chat_data[0],
            name=chat_data[1],
            last_message_time=datetime.fromisoformat(chat_data[2]) if chat_data[2] else None,
            last_message=chat_data[3],
            last_sender=chat_data[4],
            last_sender_name=None,  # This function doesn't include sender name
            last_is_from_me=chat_data[5]
        )
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()


def get_direct_chat_by_contact(user_id: str, sender_phone_number: str) -> Optional[Chat]:
    """Get chat metadata by sender phone number."""
    try:
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../whatsapp-bridge/store", user_id, "messages.db"))
        print("DB path:", db_path)
        print("CWD:", os.getcwd())
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                c.jid,
                c.name,
                c.last_message_time,
                m.content as last_message,
                m.sender as last_sender,
                m.is_from_me as last_is_from_me
            FROM chats c
            LEFT JOIN messages m ON c.jid = m.chat_jid 
                AND c.last_message_time = m.timestamp
            WHERE c.jid LIKE ? AND c.jid NOT LIKE '%@g.us'
            LIMIT 1
        """, (f"%{sender_phone_number}%",))
        
        chat_data = cursor.fetchone()
        
        if not chat_data:
            return None
            
        return Chat(
            jid=chat_data[0],
            name=chat_data[1],
            last_message_time=datetime.fromisoformat(chat_data[2]) if chat_data[2] else None,
            last_message=chat_data[3],
            last_sender=chat_data[4],
            last_sender_name=None,  # This function doesn't include sender name
            last_is_from_me=chat_data[5]
        )
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()

def get_login_status(user_id: str = None) -> dict:
    """Check the login status for a specific user."""
    if user_id is None:
        user_id = get_or_create_user_id()
    
    status_url = f"{WHATSAPP_API_BASE_URL}/login_status?user_id={user_id}"
    try:
        resp = requests.get(status_url, timeout=5)
        if resp.status_code == 200:
            status_data = resp.json()
            status = status_data.get("status", "unknown")
            
            if status == "success":
                return {
                    "success": True,
                    "status": "success",
                    "user_id": user_id,
                    "message": "Login successful! You can now use WhatsApp features."
                }
            elif status == "failed":
                return {
                    "success": False,
                    "status": "failed",
                    "user_id": user_id,
                    "message": "Login failed. Please try again."
                }
            elif status == "pending":
                return {
                    "success": False,
                    "status": "pending",
                    "user_id": user_id,
                    "message": "Waiting for QR code scan. Please scan the QR code with WhatsApp."
                }
            else:
                return {
                    "success": False,
                    "status": "unknown",
                    "user_id": user_id,
                    "message": f"Unknown login status: {status}"
                }
        else:
            return {
                "success": False,
                "status": "error",
                "user_id": user_id,
                "message": f"Error checking login status: HTTP {resp.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "status": "error",
            "user_id": user_id,
            "message": f"Error checking login status: {str(e)}"
        }

def get_qr_code(user_id: str = None) -> dict:
    """Get QR code for WhatsApp login without polling for status."""
    if user_id is None:
        user_id = get_or_create_user_id()
    
    qr_url = f"{WHATSAPP_API_BASE_URL}/qr?user_id={user_id}"
    resp = requests.get(qr_url)
    
    if resp.status_code == 200:
        # Convert QR code image to base64
        qr_base64 = base64.b64encode(resp.content).decode('utf-8')
        
        # Also save to disk for backward compatibility
        qr_path = f"{user_id}_qr.png"
        with open(qr_path, "wb") as f:
            f.write(resp.content)
        
        return {
            "success": True,
            "user_id": user_id,
            "qr_code_base64": qr_base64,
            "qr_code_path": qr_path,
            "message": f"QR code generated for user {user_id}. Please scan it with WhatsApp."
        }
    else:
        return {
            "success": False,
            "message": f"Failed to get QR code: {resp.text}"
        }

def get_contacts(user_id: str = None) -> dict:
    """Get all contacts and joined groups for a specific user."""
    if user_id is None:
        user_id = get_or_create_user_id()
    url = f"{WHATSAPP_API_BASE_URL}/contacts?user_id={user_id}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            contacts_data = response.json()
            return {
                "success": True,
                "user_id": user_id,
                "contacts": contacts_data,
                "message": f"Contacts and joined groups for user {user_id}."
            }
        else:
            return {
                "success": False,
                "message": f"Failed to get contacts: HTTP {response.status_code} - {response.text}"
            }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "message": f"Network error while fetching contacts: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error getting contacts: {str(e)}"
        }



def login(user_id: str = None):
    """Login to WhatsApp for a specific user_id using QR code."""
    if user_id is None:
        user_id = get_or_create_user_id()
    
    # Get QR code first
    qr_result = get_qr_code(user_id)
    if not qr_result["success"]:
        print(qr_result["message"])
        return False
    
    print(f"QR code generated. Please scan it with WhatsApp.")
    
    # Poll for login status
    status_url = f"{WHATSAPP_API_BASE_URL}/login_status?user_id={user_id}"
    for _ in range(300):  # Try for up to 10 minutes (300 iterations × 2 seconds)
        status_resp = requests.get(status_url)
        if status_resp.status_code == 200:
            status = status_resp.json().get("status")
            if status == "success":
                print("Login successful!")
                return True
            elif status == "failed":
                print("Login failed. Please try again.")
                return False
            else:
                print("Waiting for QR scan...")
        else:
            print("Error checking login status:", status_resp.text)
        time.sleep(2)
    print("Login timed out after 10 minutes. Please try again.")
    return False

def send_message(recipient: str, message: str, user_id: str = None) -> tuple:
    if user_id is None:
        user_id = get_or_create_user_id()
    # Validate input
    if not recipient:
        return False, "Recipient must be provided"
    url = f"{WHATSAPP_API_BASE_URL}/send?user_id={user_id}"
    payload = {
        "recipient": recipient,
        "message": message,
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        result = response.json()
        return result.get("success", False), result.get("message", "Unknown response")
    else:
        return False, f"Error: HTTP {response.status_code} - {response.text}"


def send_file(recipient: str, media_path: str, user_id: str = None) -> tuple:
    if user_id is None:
        user_id = get_or_create_user_id()
    if not recipient:
        return False, "Recipient must be provided"
    if not media_path:
        return False, "Media path must be provided"
    if not os.path.isfile(media_path):
        return False, f"Media file not found: {media_path}"
    url = f"{WHATSAPP_API_BASE_URL}/send?user_id={user_id}"
    payload = {
        "recipient": recipient,
        "media_path": media_path
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        result = response.json()
        return result.get("success", False), result.get("message", "Unknown response")
    else:
        return False, f"Error: HTTP {response.status_code} - {response.text}"


def send_audio_message(recipient: str, media_path: str, user_id: str = None) -> tuple:
    if user_id is None:
        user_id = get_or_create_user_id()
    if not recipient:
        return False, "Recipient must be provided"
    if not media_path:
        return False, "Media path must be provided"
    if not os.path.isfile(media_path):
        return False, f"Media file not found: {media_path}"
    if not media_path.endswith(".ogg"):
        try:
            media_path = audio.convert_to_opus_ogg_temp(media_path)
        except Exception as e:
            return False, f"Error converting file to opus ogg. You likely need to install ffmpeg: {str(e)}"
    url = f"{WHATSAPP_API_BASE_URL}/send?user_id={user_id}"
    payload = {
        "recipient": recipient,
        "media_path": media_path
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        result = response.json()
        return result.get("success", False), result.get("message", "Unknown response")
    else:
        return False, f"Error: HTTP {response.status_code} - {response.text}"


def download_media(user_id: Optional[str], message_id: str, chat_jid: str) -> Dict[str, Any]:
    if user_id is None:
        user_id = get_or_create_user_id()
    
    # Ensure chat_jid has the proper suffix
    if not chat_jid.endswith("@s.whatsapp.net") and not chat_jid.endswith("@g.us"):
        chat_jid = chat_jid + "@s.whatsapp.net"
    
    url = f"{WHATSAPP_API_BASE_URL}/download?user_id={user_id}"
    payload = {
        "message_id": message_id,
        "chat_jid": chat_jid
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):  # Fixed success condition check
            path = result.get("path")
            s3_url = result.get("s3_url")  # Get S3 URL if available
            filename = result.get("filename", "")
            message = result.get("message", "Media downloaded successfully")
            
            if s3_url:
                print(f"Media downloaded successfully: {path} (uploaded to S3: {s3_url})")
                return {
                    "success": True,
                    "message": message,
                    "path": path,
                    "filename": filename,
                    "s3_url": s3_url,
                    "type": "s3"
                }
            else:
                print(f"Media downloaded successfully: {path}")
                return {
                    "success": True,
                    "message": message,
                    "path": path,
                    "filename": filename,
                    "type": "file_path"
                }
        else:
            error_message = result.get('message', 'Unknown error')
            print(f"Download failed: {error_message}")
            return {
                "success": False,
                "message": error_message
            }
    else:
        error_message = f"Error: HTTP {response.status_code} - {response.text}"
        print(error_message)
        return {
            "success": False,
            "message": error_message
        }
