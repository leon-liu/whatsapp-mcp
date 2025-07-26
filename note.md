ssh -i "~/Downloads/aidirectorycrawler.pem" ubuntu@ec2-3-255-211-78.eu-west-1.compute.amazonaws.com

go version go1.24.4 linux/amd64
ubuntu@ip-172-31-11-224:~/whatsapp-mcp/whatsapp-bridge$ nohup /usr/local/go/bin/go run main.go &

Python 3.12.3
(venv) ubuntu@ip-172-31-11-224:~/whatsapp-mcp/whatsapp-mcp-server$ uv run python main.py --transport sse

Python 3.12.2
uvicorn app:app --reload --host 0.0.0.0 --port 8081

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