ssh -i "~/Downloads/aidirectorycrawler.pem" ubuntu@ec2-99-80-21-173.eu-west-1.compute.amazonaws.com


whatsapp-bridge
go version go1.24.4 linux/amd64
/usr/local/go/bin/go build -o whatsapp-bridge .
ubuntu@ip-172-31-11-224:~/whatsapp-mcp/whatsapp-bridge$ nohup ./whatsapp-bridge &
ubuntu@ip-172-31-11-224:~/whatsapp-mcp/whatsapp-bridge$ ps aux | grep whatsapp-bridge

ubuntu@ip-172-31-11-224:~/whatsapp-mcp/whatsapp-bridge$ nohup /usr/local/go/bin/go run main.go &


whatspp-mcp-server
Python 3.12.3
(venv) ubuntu@ip-172-31-11-224:~/whatsapp-mcp/whatsapp-mcp-server$ nohup uv run python main.py --transport sse &


whatspp-http-server
Python 3.12.2
pip install fastapi uvicorn
nohup uvicorn app:app --reload --host 0.0.0.0 --port 8040 &

sudo pkill -f "whatsapp-http-server"

sudo nginx -s reload


{
    "mcpServers": {
      "whatsapp": {
        "url": "http://localhost:8000/sse"
      }
    }
  }
  

  {
    "mcpServers": {
      "whatsapp": {
        "command": "/Users/liu-yang/.local/bin/uv",
        "args": [
            "--directory",
            "/Users/liu-yang/workspace/leon/ai/mcp/fork_whatsapp-mcp/whatsapp-mcp/whatsapp-mcp-server",
            "run",
            "main.py"
        ]
      }
    }
  }