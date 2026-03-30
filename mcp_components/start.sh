#!/bin/bash
# Production startup script

# Load environment variables
source .env

# Start with Uvicorn
uv run uvicorn jira_server:app \
    --host $HOST \
    --port $PORT \
    --workers $WORKERS \
    --log-level $LOG_LEVEL \
    --access-log \
    --no-use-colors
