# shared/tracing_utils.py
import httpx
import re
from langsmith import traceable

def scrub_pii(text: str) -> str:
    """Masks potential API keys, passwords, and sensitive tokens in text."""
    if not isinstance(text, str): return str(text)
    # Regex for strings > 16 chars that look like tokens/keys
    return re.sub(r'[a-zA-Z0-9]{16,}', '[REDACTED_SENSITIVE]', text)

def secure_mcp_tool(name: str, service: str = "mcp-gateway"):
    """
    Centralized decorator for top-level MCP tools.
    Automatically scrubs the final output sent to LangSmith.
    """
    return traceable(
        name=name,
        run_type="tool",
        metadata={"service": service},
        # Scrub the final return string of the tool
        process_outputs=lambda x: scrub_pii(x) 
    )

def mask_sensitive_data(inputs: dict) -> dict:
    """Generic masker for credentials in function inputs."""
    scrubbed = inputs.copy()
    if "headers" in scrubbed:
        h = scrubbed["headers"].copy()
        # Cover all common credential keys
        for key in ["Authorization", "X-Api-Key", "Cookie", "api-key"]:
            if key in h or key.lower() in h:
                h[key] = "[MASKED]"
        scrubbed["headers"] = h
    return scrubbed

def redact_output(output):
    """Generic redactor for network responses."""
    if isinstance(output, httpx.Response):
        return {
            "status_code": output.status_code,
            "latency_ms": output.elapsed.total_seconds() * 1000,
            "body": "[REDACTED_FOR_SECURITY]"
        }
    return "[REDACTED]"

def secure_trace(name: str):
    """Decorator to apply centralized security to any traceable function."""
    return traceable(
        name=name,
        run_type="tool",
        process_inputs=mask_sensitive_data,
        process_outputs=redact_output
    )
