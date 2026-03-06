#!/usr/bin/env python3
"""
Production MCP server that adds two integers
"""

import os
from fastmcp import FastMCP

# Create MCP server
mcp = FastMCP("simple-calculator")

@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Add two integers together"""
    return a + b

@mcp.tool()
def log_headers(headers: dict = None) -> str:
    """Log headers received by server"""
    if headers:
        return f"Server received headers: {list(headers.keys())}"
    else:
        return "No headers received by server"

# Create ASGI application for Uvicorn
app = mcp.http_app()
