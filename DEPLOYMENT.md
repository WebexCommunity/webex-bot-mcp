# Webex Bot MCP Server Configuration

This file provides deployment guidance and configuration options for production use.

## Production Deployment Checklist

### Security Configuration
- [ ] Bot token stored in secure environment variables (not in code)
- [ ] SSL/TLS enabled for all communications
- [ ] Regular token rotation schedule established
- [ ] Access logging enabled
- [ ] Rate limiting configured
- [ ] Input validation implemented

### Monitoring & Observability
- [ ] Application logs configured (structured logging recommended)
- [ ] Metrics collection enabled
- [ ] Health check endpoints configured
- [ ] Error tracking and alerting set up
- [ ] Performance monitoring dashboard created

### High Availability & Scale
- [ ] Container orchestration configured (if using containers)
- [ ] Load balancing configured (for HTTP transport)
- [ ] Graceful shutdown handling implemented
- [ ] Resource limits defined
- [ ] Auto-scaling policies configured

### Compliance & Governance
- [ ] Data retention policies defined
- [ ] Audit logging enabled
- [ ] Compliance framework alignment verified
- [ ] Privacy policies updated
- [ ] User consent mechanisms implemented

## Environment Variables Reference

### Required
- `WEBEX_ACCESS_TOKEN`: Bot access token from Webex Developer Portal

### Optional Configuration
- `WEBEX_DEBUG`: Enable debug logging (default: false)
- `WEBEX_RATE_LIMIT_MESSAGES_PER_SECOND`: Message rate limit (default: 10)
- `WEBEX_RATE_LIMIT_API_CALLS_PER_MINUTE`: API call rate limit (default: 300)
- `LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARN, ERROR)
- `METRICS_ENABLED`: Enable metrics collection (default: false)

### Transport Configuration
- `MCP_TRANSPORT`: Transport type (stdio, streamable-http)
- `MCP_HOST`: Host binding for HTTP transport (default: localhost)
- `MCP_PORT`: Port binding for HTTP transport (default: 8000)

## Docker Deployment

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py", "--transport", "streamable-http", "--host", "0.0.0.0"]
```

## Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webex-bot-mcp
spec:
  replicas: 2
  selector:
    matchLabels:
      app: webex-bot-mcp
  template:
    metadata:
      labels:
        app: webex-bot-mcp
    spec:
      containers:
      - name: webex-bot-mcp
        image: webex-bot-mcp:latest
        ports:
        - containerPort: 8000
        env:
        - name: WEBEX_ACCESS_TOKEN
          valueFrom:
            secretKeyRef:
              name: webex-secrets
              key: access-token
        resources:
          limits:
            memory: "512Mi"
            cpu: "500m"
          requests:
            memory: "256Mi"
            cpu: "250m"
---
apiVersion: v1
kind: Service
metadata:
  name: webex-bot-mcp-service
spec:
  selector:
    app: webex-bot-mcp
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## Claude Desktop Configuration

Add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "webex-bot": {
      "command": "python",
      "args": ["/path/to/webex-bot-mcp/main.py"],
      "env": {
        "WEBEX_ACCESS_TOKEN": "your_token_here"
      }
    }
  }
}
```

## Common Issues & Solutions

### Issue: "Token Invalid" Errors
**Solution**: Check token expiration, regenerate if needed, ensure proper environment variable setup.

### Issue: Rate Limiting
**Solution**: Implement exponential backoff, respect API limits, consider request batching.

### Issue: Memory Usage
**Solution**: Monitor for memory leaks, implement connection pooling, tune garbage collection.

### Issue: High Latency
**Solution**: Use connection pooling, implement caching, optimize database queries if used.

## Performance Tuning

### Message Throughput Optimization
- Use bulk operations where possible
- Implement message queuing for high-volume scenarios
- Consider async/await patterns for concurrent operations

### Resource Optimization
- Connection pooling for HTTP transport
- Memory-efficient data structures
- Proper cleanup of resources

### Monitoring Metrics
- Message send success rate
- API response times
- Error rates by operation type
- Resource utilization (CPU, memory, network)

## Security Best Practices

### Token Management
- Store tokens in secure key management systems
- Implement token rotation automation
- Monitor for token compromise

### Network Security
- Use HTTPS only in production
- Implement proper firewall rules
- Consider VPN or private network deployment

### Data Protection
- Encrypt sensitive data at rest
- Implement audit logging
- Follow data retention policies
- Regular security assessments
