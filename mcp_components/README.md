# MCP Components

A collection of Model Context Protocol (MCP) servers, proxies, and testing tools for building AI-powered integrations with external services like Jira.

## Architecture Overview

This project provides a modular MCP ecosystem with the following components:

- **MCP Servers** - FastAPI-based servers exposing tools via MCP protocol
- **Proxy Services** - HTTP proxies that translate REST calls to MCP tool calls  
- **Testing Suite** - Comprehensive test clients for validation
- **Container Support** - Docker deployment with observability

## Core Components

### `jira_server.py`
**Primary Jira MCP Server** - Exposes Jira issue lookup functionality as MCP tools.

**Key Features:**
- FastMCP-based server with `get_issue_details()` tool
- Basic Auth integration with Jira API v2
- Input validation and error handling
- Runs on port 8011 by default

**Usage:**
```bash
uv run uvicorn jira_server:app --host 0.0.0.0 --port 8011 --reload
```

### `mcp_proxy.py`
**HTTP-to-MCP Proxy** - Translates REST API calls to MCP tool invocations.

**Features:**
- Manages MCP session lifecycle
- Exposes `/jira_lookup` REST endpoint
- Handles SSE response parsing
- Routes to MCP servers on port 8020

**Usage:**
```bash
uv run uvicorn mcp_proxy:app --host 0.0.0.0 --port 8000
```

## Container Deployment

### `jira_container/`
**Production-ready Jira MCP container** with enhanced observability.

**Files:**
- `jira_server_langsmith.py` - Jira server with LangSmith tracing
- `dockerfile` - Multi-stage Docker build
- `requirements.txt` - Container dependencies
- `shared/tracing_utils.py` - Observability utilities

**Build & Run:**
```bash
# Build container
docker build -t mcp-jira-gateway:latest .

# Run with environment
docker run -p 8020:8020 --env-file .env mcp-jira-gateway:latest
```

## Testing Suite

### Test Files Overview

| Test File | Purpose | Target |
|-----------|---------|--------|
| `test_simple.py` | Direct MCP tool calls | `jira_server.py` |
| `test_jira_mcp.py` | Jira MCP integration | `jira_server.py` |
| `test_jira_thru_kong.py` | Kong gateway routing | Kong + MCP |
| `test_kong_mcp.py` | Kong proxy validation | Kong endpoints |
| `test_headers.py` | Header validation | All servers |

### Running Tests

```bash
# Test direct MCP tool calls
uv run python test_simple.py

# Test Jira integration
uv run python test_jira_mcp.py

# Test through Kong gateway
uv run python test_jira_thru_kong.py
```

## Development Workflow

### 1. Local Development
```bash
# Start Jira MCP server
uv run uvicorn jira_server:app --host 0.0.0.0 --port 8011 --reload

# Test with MCP client
uv run python test_jira_mcp.py
```

### 2. Proxy Development
```bash
# Start proxy service
uv run uvicorn mcp_proxy:app --host 0.0.0.0 --port 8000

# Test REST->MCP translation
curl -X POST http://localhost:8000/jira_lookup \
  -H "Content-Type: application/json" \
  -d '{"ticket": "KAN-65"}'
```

### 3. Container Deployment
```bash
# Build and deploy container
docker build --no-cache -t mcp-jira-gateway:latest .
docker run -p 8020:8020 --env-file .env mcp-jira-gateway:latest
```

### 4. Production Startup
```bash
# Using start script with environment variables
source .env
./start.sh
```

## Environment Configuration

Create `.env` file with:
```bash
# Jira Configuration
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_KEY=your-api-token

# Server Configuration  
HOST=0.0.0.0
PORT=8011
WORKERS=4
LOG_LEVEL=info

# LangSmith (optional)
LANGCHAIN_PROJECT=mcp-jira-gateway
LANGCHAIN_TRACING_V2=true
```

## Dependencies

Key packages from `pyproject.toml`:
- `fastmcp>=3.1.0` - MCP server framework
- `fastapi>=0.135.1` - ASGI web framework  
- `httpx>=0.28.1` - Async HTTP client
- `python-dotenv>=1.2.2` - Environment management
- `uvicorn>=0.41.0` - ASGI server
- `langsmith>=0.7.13` - Observability (optional)

## Port Allocation

| Service | Default Port | Purpose |
|---------|-------------|---------|
| `jira_server.py` | 8011 | Jira MCP server |
| `mcp_proxy.py` | 8000 | HTTP proxy |
| Container | 8020 | Production Jira service |
| Kong Gateway | 9050 | API gateway (if used) |

## MCP Protocol Flow

1. **Session Creation** - Client connects to `/mcp` endpoint
2. **Protocol Init** - JSON-RPC `initialize` method
3. **Tool Call** - JSON-RPC `tools/call` with parameters  
4. **Response** - SSE stream with structured results
5. **Session Cleanup** - Automatic or manual termination

## Observability

The `jira_container` includes LangSmith integration for:
- Request/response tracing
- Tool execution monitoring  
- Performance metrics
- Error tracking

Enable with `LANGCHAIN_TRACING_V2=true` in environment.
