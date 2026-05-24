# AWS Deployment Guide — Webex Bot MCP

This guide covers deploying the server on an EC2 instance with an Application Load Balancer
providing TLS termination.

```
MCP Client
    │  HTTPS :443  Authorization: Bearer <webex_token>
    ▼
┌─────────────────────────────────┐
│  Application Load Balancer      │  ← ACM certificate (TLS termination)
│  Listener: HTTPS 443            │
└──────────────┬──────────────────┘
               │  HTTP :8000
               ▼
┌─────────────────────────────────┐
│  EC2 instance                   │
│  docker-compose                 │
│  webex-bot-mcp container :8000  │
└─────────────────────────────────┘
```

## Prerequisites

- AWS account with permissions to create EC2, ALB, ACM, and security group resources
- A domain name with DNS you can update (required for the ACM certificate)
- Docker and Docker Compose installed on the EC2 instance

## 1. Build and push the image

Build locally and push to ECR, or build directly on the instance.

**Option A — build on the EC2 instance (simpler):**
```bash
git clone https://github.com/WebexCommunity/webex-bot-mcp.git
cd webex-bot-mcp
docker compose build
```

**Option B — ECR:**
```bash
aws ecr create-repository --repository-name webex-bot-mcp
# follow the ECR push commands shown in the console
```

## 2. Security groups

Create two security groups.

**ALB security group (`sg-alb`):**
| Type  | Protocol | Port | Source    |
|-------|----------|------|-----------|
| HTTPS | TCP      | 443  | 0.0.0.0/0 |

**EC2 security group (`sg-ec2`):**
| Type        | Protocol | Port | Source   |
|-------------|----------|------|----------|
| Custom TCP  | TCP      | 8000 | sg-alb   |
| SSH         | TCP      | 22   | your IP  |

Port 8000 is only reachable from the ALB — never directly from the internet.

## 3. ACM certificate

1. Go to **AWS Certificate Manager → Request certificate**
2. Request a public certificate for your domain (e.g. `mcp.example.com`)
3. Validate via DNS — add the CNAME record ACM gives you to your DNS provider
4. Wait for status to show **Issued** before continuing

## 4. Target group

1. Go to **EC2 → Target Groups → Create target group**
2. Settings:
   - Target type: **Instances**
   - Protocol: **HTTP**, Port: **8000**
   - Health check path: **`/health`**
   - Healthy threshold: 2, Unhealthy threshold: 3, Interval: 30s
3. Register your EC2 instance as a target

## 5. Application Load Balancer

1. Go to **EC2 → Load Balancers → Create load balancer → Application Load Balancer**
2. Settings:
   - Scheme: **Internet-facing**
   - IP address type: **IPv4**
   - VPC and subnets: select at least two AZs
   - Security group: `sg-alb`
3. **Listeners:**
   - HTTPS :443 → forward to your target group
   - Select your ACM certificate
4. Create the load balancer and note the DNS name (e.g. `my-alb-123456.us-east-1.elb.amazonaws.com`)

## 6. DNS

Add a CNAME record pointing your domain to the ALB DNS name:
```
mcp.example.com  CNAME  my-alb-123456.us-east-1.elb.amazonaws.com
```

## 7. Run the container

On the EC2 instance:
```bash
cd webex-bot-mcp
docker compose up -d
```

No environment variables are required — each MCP client supplies its own Webex bot token
via the `Authorization: Bearer` header. If you want to run in stdio mode on the same host
you can still set `WEBEX_ACCESS_TOKEN` in a `.env` file.

## 8. Verify

```bash
# Health check (no auth required)
curl https://mcp.example.com/health
# → {"status":"ok"}

# Confirm auth is enforced on the MCP endpoint
curl https://mcp.example.com/mcp
# → 401 Authorization: Bearer <webex_bot_token> header required
```

## 9. MCP client configuration

Point your MCP client at the HTTPS URL. Example for Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "webex-bot": {
      "url": "https://mcp.example.com/mcp",
      "headers": {
        "Authorization": "Bearer <your_webex_bot_token>"
      }
    }
  }
}
```

Each user or team connects with their own Webex bot token. The server itself holds no token.

## Environment variables reference

All variables are optional for HTTP transport.

| Variable | Default | Description |
|---|---|---|
| `WEBEX_ACCESS_TOKEN` | — | Token for stdio transport only |
| `WEBEX_DEBUG` | `false` | Enable verbose logging |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `LOG_FORMAT` | `text` | `text` or `json` |
| `METRICS_ENABLED` | `false` | Enable Prometheus metrics |

## Scaling note

MCP sessions are stateful — a client initializes a session and reuses it for subsequent
tool calls. If you run multiple EC2 instances behind the ALB, enable **sticky sessions**
(duration-based) on the target group so all requests from one client land on the same
instance. A single instance is fine for most deployments.
