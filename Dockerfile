# Multi-stage build for Webex Bot MCP Server
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy everything needed for a PEP 517 build
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

# Non-editable install so the package lands fully in site-packages
RUN pip install --no-cache-dir .


FROM python:3.12-slim AS production

RUN groupadd -r webexbot && useradd -r -g webexbot webexbot

RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/webex-bot-mcp* /usr/local/bin/

RUN chown -R webexbot:webexbot /app

USER webexbot

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD webex-bot-mcp-health --skip-api --exit-code || exit 1

CMD ["webex-bot-mcp", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8000"]

LABEL maintainer="Webex Bot MCP Team"
LABEL description="Webex Bot Model Context Protocol Server"
LABEL version="1.0.0"
