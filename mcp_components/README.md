uv run uvicorn jira_server:app --host 0.0.0.0 --port 8011 --reload
docker build -t mcp-jira-gateway:latest .
docker build --no-cache -t mcp-jira-gateway:latest .
docker run -p 8020:8020 --env-file .env mcp-jira-gateway:latest
