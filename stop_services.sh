#!/bin/bash

# WhatsApp MCP Services Stop Script
# This script stops all running WhatsApp MCP services

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

# Function to stop a process
stop_process() {
    local process_name="$1"
    local service_name="$2"
    
    if is_process_running "$process_name"; then
        print_status "Stopping $service_name..."
        sudo pkill -f "$process_name" || true
        sleep 2
        
        if is_process_running "$process_name"; then
            print_warning "Force killing $service_name..."
            sudo pkill -9 -f "$process_name" || true
            sleep 1
        fi
        
        if is_process_running "$process_name"; then
            print_error "Failed to stop $service_name"
            return 1
        else
            print_success "$service_name stopped successfully"
            return 0
        fi
    else
        print_status "$service_name is not running"
        return 0
    fi
}

# Main stop function
main() {
    echo "=========================================="
    echo "WhatsApp MCP Services Stop Script"
    echo "=========================================="
    
    local all_stopped=true
    
    # Stop WhatsApp Bridge
    echo ""
    echo "=========================================="
    echo "Stopping WhatsApp Bridge..."
    echo "=========================================="
    
    if ! stop_process "./whatsapp-bridge" "WhatsApp Bridge"; then
        all_stopped=false
    fi
    
    # Stop WhatsApp HTTP Server
    echo ""
    echo "=========================================="
    echo "Stopping WhatsApp HTTP Server..."
    echo "=========================================="
    
    if ! stop_process "uvicorn app:app" "WhatsApp HTTP Server"; then
        all_stopped=false
    fi
    
    # Stop WhatsApp MCP Server
    echo ""
    echo "=========================================="
    echo "Stopping WhatsApp MCP Server..."
    echo "=========================================="
    
    if ! stop_process "python main.py --transport sse" "WhatsApp MCP Server"; then
        all_stopped=false
    fi
    
    # Final status check
    echo ""
    echo "=========================================="
    echo "Final Status Check"
    echo "=========================================="
    
    print_status "Checking if all services are stopped..."
    
    local bridge_running=false
    local http_server_running=false
    local mcp_server_running=false
    
    if is_process_running "./whatsapp-bridge"; then
        print_error "✗ WhatsApp Bridge is still running"
        bridge_running=true
    else
        print_success "✓ WhatsApp Bridge is stopped"
    fi
    
    if is_process_running "uvicorn app:app"; then
        print_error "✗ WhatsApp HTTP Server is still running"
        http_server_running=true
    else
        print_success "✓ WhatsApp HTTP Server is stopped"
    fi
    
    if is_process_running "python main.py --transport sse"; then
        print_error "✗ WhatsApp MCP Server is still running"
        mcp_server_running=true
    else
        print_success "✓ WhatsApp MCP Server is stopped"
    fi
    
    echo ""
    if [ "$bridge_running" = false ] && [ "$http_server_running" = false ] && [ "$mcp_server_running" = false ]; then
        echo "=========================================="
        print_success "All services stopped successfully!"
        echo "=========================================="
    else
        echo "=========================================="
        print_warning "Some services may still be running"
        echo "=========================================="
        print_status "You may need to manually stop remaining services:"
        if [ "$bridge_running" = true ]; then
            echo "  • sudo pkill -9 -f './whatsapp-bridge'"
        fi
        if [ "$http_server_running" = true ]; then
            echo "  • sudo pkill -9 -f 'uvicorn app:app'"
        fi
        if [ "$mcp_server_running" = true ]; then
            echo "  • sudo pkill -9 -f 'python main.py --transport sse'"
        fi
    fi
    echo ""
}

# Run the main function
main "$@"
