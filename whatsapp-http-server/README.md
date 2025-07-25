# WhatsApp HTTP Server

This project exposes a RESTful API to access WhatsApp chat data using the `list_chats` function from the main WhatsApp MCP server.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the server (default):
   ```bash
   uvicorn app:app --reload
   ```

   To specify a custom host and port (e.g., host 0.0.0.0 and port 8081):
   ```bash
   uvicorn app:app --reload --host 0.0.0.0 --port 8081
   ```

## API

### GET /chats

Query Parameters:
- `user_id` (required): The user ID to fetch chats for
- `query` (optional): Search term for chat name or JID
- `limit` (optional): Number of results to return (default: 20)
- `page` (optional): Page number for pagination (default: 0)
- `include_last_message` (optional): Whether to include last message info (default: true)
- `sort_by` (optional): Sort by 'last_active' or 'name' (default: 'last_active')

Example:
```bash
curl 'http://localhost:8000/chats?user_id=leon'
``` 