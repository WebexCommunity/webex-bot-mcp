# Multi-stage build for Webex Bot MCP Server
FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Production stage
FROM python:3.12-slim as production

# Create non-root user for security
RUN groupadd -r webexbot && useradd -r -g webexbot webexbot

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY main.py ./
COPY tools/ ./tools/
COPY config.py ./
COPY health_check.py ./
COPY .env.template ./

# Change ownership to non-root user
RUN chown -R webexbot:webexbot /app

# Switch to non-root user
USER webexbot

# Create volume for configuration
VOLUME ["/app/config"]

# Expose port for HTTP transport
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python health_check.py --skip-rooms --exit-code || exit 1

# Default command
CMD ["python", "main.py", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8000"]

# Metadata
LABEL maintainer="Webex Bot MCP Team"
LABEL description="Webex Bot Model Context Protocol Server"
LABEL version="1.0.0"
