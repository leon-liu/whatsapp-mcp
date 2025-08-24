# WhatsApp MCP Service Management Scripts

This directory contains automated scripts to manage all WhatsApp MCP services. These scripts replace the manual steps outlined in `steps.sh` with automated, robust service management.

## Available Scripts

### 1. `start_services.sh` - Start All Services
Automatically starts all WhatsApp MCP services in the correct order:
- WhatsApp Bridge (Go service)
- WhatsApp HTTP Server (Python/FastAPI service on port 8040)
- WhatsApp MCP Server (Python service with SSE transport)

**Features:**
- Automatic dependency checking
- Process cleanup before starting
- Service health verification
- Colored output for easy reading
- Comprehensive error handling
- Git pull for latest code

**Usage:**
```bash
./start_services.sh
```

### 2. `stop_services.sh` - Stop All Services
Gracefully stops all running WhatsApp MCP services.

**Features:**
- Graceful shutdown with fallback to force kill
- Status verification after stopping
- Clear feedback on what was stopped

**Usage:**
```bash
./stop_services.sh
```

### 3. `check_status.sh` - Check Service Status
Monitors the status of all services with detailed information.

**Features:**
- Process status checking
- Port availability verification
- Resource usage monitoring (CPU, Memory, Uptime)
- Quick action suggestions

**Usage:**
```bash
./check_status.sh
```

## Prerequisites

Before using these scripts, ensure you have:

1. **Virtual Environments**: Both Python services require virtual environments
   ```bash
   # For whatsapp-http-server
   cd whatsapp-http-server
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # For whatsapp-mcp-server
   cd whatsapp-mcp-server
   python -m venv venv
   source venv/bin/activate
   uv sync
   ```

2. **Go Installation**: The WhatsApp Bridge requires Go to be installed at `/usr/local/go/bin/go`

3. **Network Tools**: The `nc` (netcat) command for port checking

4. **Sudo Access**: Required for process management

## Quick Start

1. **Start all services:**
   ```bash
   ./start_services.sh
   ```

2. **Check service status:**
   ```bash
   ./check_status.sh
   ```

3. **Stop all services:**
   ```bash
   ./stop_services.sh
   ```

## Service Details

### WhatsApp Bridge
- **Type**: Go binary
- **Process**: `./whatsapp-bridge`
- **Logs**: `~/whatsapp-mcp/whatsapp-bridge/nohup.out`
- **Auto-restart**: No (manual restart required)

### WhatsApp HTTP Server
- **Type**: Python/FastAPI with Uvicorn
- **Process**: `uvicorn app:app`
- **Port**: 8040
- **Logs**: `~/whatsapp-mcp/whatsapp-http-server/nohup.out`
- **Auto-restart**: Yes (with --reload flag)

### WhatsApp MCP Server
- **Type**: Python with UV
- **Process**: `python main.py --transport sse`
- **Logs**: `~/whatsapp-mcp/whatsapp-mcp-server/nohup.out`
- **Auto-restart**: No (manual restart required)

## Troubleshooting

### Common Issues

1. **Virtual Environment Not Found**
   - Create virtual environments as shown in Prerequisites
   - Ensure you're in the correct directory

2. **Permission Denied**
   - Ensure scripts are executable: `chmod +x *.sh`
   - Check sudo access for process management

3. **Port Already in Use**
   - Use `./stop_services.sh` to stop all services first
   - Check for other processes using port 8040

4. **Go Build Fails**
   - Verify Go installation: `which go`
   - Check Go version: `go version`

### Manual Process Management

If scripts fail, you can manually manage processes:

```bash
# Find processes
ps aux | grep whatsapp-bridge
ps aux | grep uvicorn
ps aux | grep "python main.py"

# Kill processes
sudo pkill -f whatsapp-bridge
sudo pkill -f uvicorn
sudo pkill -f "python main.py"

# Force kill if needed
sudo pkill -9 -f whatsapp-bridge
sudo pkill -9 -f uvicorn
sudo pkill -9 -f "python main.py"
```

## Log Monitoring

Monitor service logs in real-time:

```bash
# Bridge logs
tail -f ~/whatsapp-mcp/whatsapp-bridge/nohup.out

# HTTP Server logs
tail -f ~/whatsapp-mcp/whatsapp-http-server/nohup.out

# MCP Server logs
tail -f ~/whatsapp-mcp/whatsapp-mcp-server/nohup.out
```

## Script Customization

The scripts are designed to be easily customizable:

- **Ports**: Modify port numbers in the scripts
- **Paths**: Update directory paths if needed
- **Timeouts**: Adjust wait times and retry attempts
- **Dependencies**: Add or remove service dependencies

## Security Notes

- Scripts use `sudo` for process management
- Ensure scripts are only accessible to authorized users
- Review and understand what the scripts do before running
- Consider using a dedicated service user for production environments

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify all prerequisites are met
3. Check service logs for error messages
4. Ensure you have the latest code from git
