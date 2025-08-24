#!/bin/bash

# WhatsApp MCP Services Startup Script
# This script starts all required services for the WhatsApp MCP system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a process is running
is_process_running() {
    local process_name="$1"
    pgrep -f "$process_name" > /dev/null 2>&1
}

# Function to kill a process if it's running
kill_process() {
    local process_name="$1"
    local service_name="$2"
    
    if is_process_running "$process_name"; then
        print_status "Stopping $service_name..."
        sudo pkill -f "$process_name" || true
        sleep 2
        if is_process_running "$process_name"; then
            print_warning "Force killing $service_name..."
            sudo pkill -9 -f "$process_name" || true
        fi
        print_success "$service_name stopped"
    else
        print_status "$service_name is not running"
    fi
}

# Function to wait for a service to be ready
wait_for_service() {
    local service_name="$1"
    local port="$2"
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $service_name to be ready on port $port..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z localhost $port 2>/dev/null; then
            print_success "$service_name is ready on port $port"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start within $((max_attempts * 2)) seconds"
    return 1
}

# Main startup function
main() {
    echo "=========================================="
    echo "WhatsApp MCP Services Startup Script"
    echo "=========================================="
    
    # Navigate to the main directory
    cd ~/whatsapp-mcp || {
        print_error "Failed to navigate to ~/whatsapp-mcp"
        exit 1
    }
    
    # Git pull latest code
    print_status "Pulling latest code from git..."
    git pull || {
        print_warning "Git pull failed, continuing with existing code..."
    }
    
    # 1. Start WhatsApp Bridge
    echo ""
    echo "=========================================="
    echo "Starting WhatsApp Bridge..."
    echo "=========================================="
    
    cd ~/whatsapp-mcp/whatsapp-bridge || {
        print_error "Failed to navigate to whatsapp-bridge directory"
        exit 1
    }
    
    # Build the bridge
    print_status "Building WhatsApp Bridge..."
    /usr/local/go/bin/go build -o whatsapp-bridge . || {
        print_error "Failed to build WhatsApp Bridge"
        exit 1
    }
    
    # Kill existing process
    kill_process "./whatsapp-bridge" "WhatsApp Bridge"
    
    # Start the bridge
    print_status "Starting WhatsApp Bridge..."
    nohup ./whatsapp-bridge > nohup.out 2>&1 &
    sleep 3
    
    # Check if bridge started successfully
    if is_process_running "./whatsapp-bridge"; then
        print_success "WhatsApp Bridge started successfully"
        print_status "Bridge logs (last 10 lines):"
        tail -10 nohup.out 2>/dev/null || echo "No logs available yet"
    else
        print_error "WhatsApp Bridge failed to start"
        print_status "Bridge logs:"
        cat nohup.out 2>/dev/null || echo "No logs available"
        exit 1
    fi
    
    # 2. Start WhatsApp HTTP Server
    echo ""
    echo "=========================================="
    echo "Starting WhatsApp HTTP Server..."
    echo "=========================================="
    
    cd ~/whatsapp-mcp/whatsapp-http-server || {
        print_error "Failed to navigate to whatsapp-http-server directory"
        exit 1
    }
    
    # Activate virtual environment
    if [ ! -d "venv" ]; then
        print_error "Virtual environment not found. Please create it first:"
        print_status "python -m venv venv"
        print_status "source venv/bin/activate"
        print_status "pip install -r requirements.txt"
        exit 1
    fi
    
    source venv/bin/activate
    
    # Kill existing process
    kill_process "whatsapp-http-server" "WhatsApp HTTP Server"
    
    # Start the HTTP server
    print_status "Starting WhatsApp HTTP Server on port 8040..."
    nohup uvicorn app:app --reload --host 0.0.0.0 --port 8040 > nohup.out 2>&1 &
    sleep 3
    
    # Check if HTTP server started successfully
    if is_process_running "uvicorn app:app"; then
        print_success "WhatsApp HTTP Server started successfully"
        print_status "HTTP Server logs (last 10 lines):"
        tail -10 nohup.out 2>/dev/null || echo "No logs available yet"
        
        # Wait for service to be ready
        wait_for_service "WhatsApp HTTP Server" 8040
    else
        print_error "WhatsApp HTTP Server failed to start"
        print_status "HTTP Server logs:"
        cat nohup.out 2>/dev/null || echo "No logs available"
        deactivate
        exit 1
    fi
    
    deactivate
    
    # 3. Start WhatsApp MCP Server
    echo ""
    echo "=========================================="
    echo "Starting WhatsApp MCP Server..."
    echo "=========================================="
    
    cd ~/whatsapp-mcp/whatsapp-mcp-server || {
        print_error "Failed to navigate to whatsapp-mcp-server directory"
        exit 1
    }
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_error "Virtual environment not found. Please create it first:"
        print_status "python -m venv venv"
        print_status "source venv/bin/activate"
        print_status "uv sync"
        exit 1
    fi
    
    source venv/bin/activate
    
    # Kill existing process
    kill_process "python main.py --transport sse" "WhatsApp MCP Server"
    
    # Start the MCP server
    print_status "Starting WhatsApp MCP Server..."
    nohup uv run python main.py --transport sse > nohup.out 2>&1 &
    sleep 3
    
    # Check if MCP server started successfully
    if is_process_running "python main.py --transport sse"; then
        print_success "WhatsApp MCP Server started successfully"
        print_status "MCP Server logs (last 10 lines):"
        tail -10 nohup.out 2>/dev/null || echo "No logs available yet"
    else
        print_error "WhatsApp MCP Server failed to start"
        print_status "MCP Server logs:"
        cat nohup.out 2>/dev/null || echo "No logs available"
        deactivate
        exit 1
    fi
    
    deactivate
    
    # Final status check
    echo ""
    echo "=========================================="
    echo "Final Status Check"
    echo "=========================================="
    
    print_status "Checking all services..."
    
    if is_process_running "./whatsapp-bridge"; then
        print_success "✓ WhatsApp Bridge is running"
    else
        print_error "✗ WhatsApp Bridge is not running"
    fi
    
    if is_process_running "uvicorn app:app"; then
        print_success "✓ WhatsApp HTTP Server is running"
    else
        print_error "✗ WhatsApp HTTP Server is not running"
    fi
    
    if is_process_running "python main.py --transport sse"; then
        print_success "✓ WhatsApp MCP Server is running"
    else
        print_error "✗ WhatsApp MCP Server is not running"
    fi
    
    echo ""
    echo "=========================================="
    print_success "All services started successfully!"
    echo "=========================================="
    echo ""
    print_status "Service endpoints:"
    echo "  • WhatsApp Bridge: Running as background process"
    echo "  • WhatsApp HTTP Server: http://localhost:8040"
    echo "  • WhatsApp MCP Server: Running with SSE transport"
    echo ""
    print_status "To view logs, use:"
    echo "  • Bridge logs: tail -f ~/whatsapp-mcp/whatsapp-bridge/nohup.out"
    echo "  • HTTP Server logs: tail -f ~/whatsapp-mcp/whatsapp-http-server/nohup.out"
    echo "  • MCP Server logs: tail -f ~/whatsapp-mcp/whatsapp-mcp-server/nohup.out"
    echo ""
}

# Run the main function
main "$@"
