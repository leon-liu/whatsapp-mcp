1. navigate to folder ~/whatsapp-mcp
2. git pull get latest code
3. cd whatsapp-bridge folder
4. /usr/local/go/bin/go build -o whatsapp-bridge .
5. ps aux | grep ./whatsapp-bridge find out pid e.g. 87502
6. kill -9 the pid from step 5 or merge 5 and 6 to use sudo pkill -f "whatsapp-bridge"
7. nohup ./whatsapp-bridge &
8. ps aux | grep ./whatsapp-bridge or tail -100 nohup.out to check status



1. cd ~/whatsapp-mcp/whatsapp-http-server/
2. source venv/bin/activate
3. sudo pkill -f "whatsapp-http-server"
4. nohup uvicorn app:app --reload --host 0.0.0.0 --port 8040 &
5. tail -100 nohup.out to check status
6. deactivate

1. cd ~/whatsapp-mcp/whatsapp-mcp-server/
2. source venv/bin/activate
3. sudo pkill -f "python main.py --transport sse"
4. nohup uv run python main.py --transport sse &
5. tail -100 nohup.out to check status
6. deactivate