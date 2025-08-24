#!/bin/bash

# WhatsApp MCP Services Status Check Script
# This script checks the status of all WhatsApp MCP services

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

# Function to get process info
get_process_info() {
    local process_name="$1"
    local pid=$(pgrep -f "$process_name" | head -1)
    if [ -n "$pid" ]; then
        local uptime=$(ps -o etime= -p "$pid" 2>/dev/null | tr -d ' ')
        local memory=$(ps -o rss= -p "$pid" 2>/dev/null | tr -d ' ')
        local cpu=$(ps -o %cpu= -p "$pid" 2>/dev/null | tr -d ' ')
        echo "$pid|$uptime|$memory|$cpu"
    fi
}

# Function to check service status
check_service() {
    local process_name="$1"
    local service_name="$2"
    local port="$3"
    
    if is_process_running "$process_name"; then
        local process_info=$(get_process_info "$process_name")
        if [ -n "$process_info" ]; then
            IFS='|' read -r pid uptime memory cpu <<< "$process_info"
            print_success "✓ $service_name is running"
            echo "    PID: $pid"
            echo "    Uptime: $uptime"
            echo "    Memory: ${memory}KB"
            echo "    CPU: ${cpu}%"
            
            # Check if port is listening (if specified)
            if [ -n "$port" ]; then
                if nc -z localhost $port 2>/dev/null; then
                    echo "    Port $port: Listening ✓"
                else
                    echo "    Port $port: Not listening ✗"
                fi
            fi
        else
            print_success "✓ $service_name is running"
        fi
        return 0
    else
        print_error "✗ $service_name is not running"
        return 1
    fi
}

# Main status check function
main() {
    echo "=========================================="
    echo "WhatsApp MCP Services Status Check"
    echo "=========================================="
    echo "Timestamp: $(date)"
    echo ""
    
    local all_running=true
    
    # Check WhatsApp Bridge
    echo "=========================================="
    echo "WhatsApp Bridge Status"
    echo "=========================================="
    
    if ! check_service "./whatsapp-bridge" "WhatsApp Bridge"; then
        all_running=false
    fi
    
    # Check WhatsApp HTTP Server
    echo ""
    echo "=========================================="
    echo "WhatsApp HTTP Server Status"
    echo "=========================================="
    
    if ! check_service "uvicorn app:app" "WhatsApp HTTP Server" "8040"; then
        all_running=false
    fi
    
    # Check WhatsApp MCP Server
    echo ""
    echo "=========================================="
    echo "WhatsApp MCP Server Status"
    echo "=========================================="
    
    if ! check_service "python main.py --transport sse" "WhatsApp MCP Server"; then
        all_running=false
    fi
    
    # Summary
    echo ""
    echo "=========================================="
    echo "Summary"
    echo "=========================================="
    
    if [ "$all_running" = true ]; then
        print_success "All services are running!"
    else
        print_warning "Some services are not running"
    fi
    
    echo ""
    print_status "Quick Actions:"
    echo "  • Start all services: ./start_services.sh"
    echo "  • Stop all services: ./stop_services.sh"
    echo "  • Check status again: ./check_status.sh"
    echo ""
    print_status "Log locations:"
    echo "  • Bridge: ~/whatsapp-mcp/whatsapp-bridge/nohup.out"
    echo "  • HTTP Server: ~/whatsapp-mcp/whatsapp-http-server/nohup.out"
    echo "  • MCP Server: ~/whatsapp-mcp/whatsapp-mcp-server/nohup.out"
    echo ""
}

# Run the main function
main "$@"
