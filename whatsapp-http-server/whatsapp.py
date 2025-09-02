import sqlite3
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import os

@dataclass
class Chat:
    jid: str
    name: Optional[str]
    last_message_time: Optional[datetime]
    last_message: Optional[str] = None
    last_sender: Optional[str] = None
    last_sender_name: Optional[str] = None
    last_is_from_me: Optional[bool] = None
    media_type: Optional[str] = None
    message_id: Optional[str] = None
    message_timestamp: Optional[datetime] = None

    def to_dict(self):
        return {
            'jid': self.jid,
            'name': self.name,
            'last_message_time': self.last_message_time.isoformat() if self.last_message_time else None,
            'last_message': self.last_message,
            'last_sender': self.last_sender,
            'last_sender_name': self.last_sender_name,
            'last_is_from_me': self.last_is_from_me,
            'media_type': self.media_type,
            'message_id': self.message_id,
            'message_timestamp': self.message_timestamp.isoformat() if self.message_timestamp else None,
        }

def list_chats(
    user_id: str,
    query: Optional[str] = None,
    limit: int = 2000,
    page: int = 0,
    include_last_message: bool = True,
    sort_by: str = "last_active"
) -> List[Chat]:
    """Get group chats matching the specified criteria (only JIDs ending with @g.us)."""
    try:
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../whatsapp-bridge/store", user_id, "messages.db"))
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
                messages.media_type as last_media_type,
                messages.id as message_id,
                messages.timestamp as message_timestamp,
                sender_chat.name as last_sender_name
            FROM chats
        """]

        if include_last_message:
            query_parts.append("""
                LEFT JOIN messages ON chats.jid = messages.chat_jid
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
        offset = (page) * limit
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
                last_sender_name=chat_data[9],
                last_is_from_me=chat_data[5],
                media_type=chat_data[6],
                message_id=chat_data[7],
                message_timestamp=datetime.fromisoformat(chat_data[8]) if chat_data[8] else None
            )
            result.append(chat)

        return result

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close() 

def get_allowed_contacts(user_id: str) -> dict:
    """Get all allowed contacts for a specific user by reading directly from the database."""
    try:
        # Path to the user's messages.db file
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../whatsapp-bridge/store", user_id, "messages.db"))
        print("DB path:", db_path)
        print("CWD:", os.getcwd())
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Query to get only allowed GROUP contacts (JID ending with @g.us)
        cursor.execute("""
            SELECT 
                jid,
                name,
                last_message_time,
                is_allowed,
                unread_count
            FROM chats
            WHERE is_allowed = TRUE AND jid LIKE '%@g.us'
            ORDER BY name, jid
        """)
        
        allowed_chats = cursor.fetchall()
        
        result = []
        for chat_data in allowed_chats:
            chat = {
                'jid': chat_data[0],
                'name': chat_data[1],
                'last_message_time': chat_data[2],
                'is_allowed': bool(chat_data[3]),
                'unread_count': chat_data[4],
                'is_group': chat_data[0].endswith("@g.us")
            }
            result.append(chat)
            
        return {
            "success": True,
            "user_id": user_id,
            "allowed_contacts": result,
            "count": len(result),
            "message": f"Found {len(result)} allowed group contacts for user {user_id}."
        }
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return {
            "success": False,
            "user_id": user_id,
            "message": f"Database error while fetching allowed contacts: {str(e)}"
        }
    except Exception as e:
        print(f"Error: {e}")
        return {
            "success": False,
            "user_id": user_id,
            "message": f"Error getting allowed contacts: {str(e)}"
        }
    finally:
        if 'conn' in locals():
            conn.close() 