# HyperGraphRAG Deployment Guide

This guide covers deployment options for the HyperGraphRAG Visualization system.

## Table of Contents

- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites

- Docker and Docker Compose (for containerized deployment)
- Python 3.10+ (for local development)
- Node.js 20+ and pnpm (for frontend development)
- OpenAI API key

### 1. Clone and Configure

```bash
# Clone the repository
git clone <repository-url>
cd HyperGraphRAG

# Copy environment file
cp .env.docker .env

# Edit .env and add your OpenAI API key
nano .env
```

### 2. Start with Docker

```bash
# Build and start all services
./scripts/docker-up.sh --build

# Access the application
# Frontend: http://localhost
# Backend API: http://localhost:3401
# API Docs: http://localhost:3401/docs
```

## Development Setup

### Local Development (Recommended)

Run backend and frontend locally without Docker:

```bash
# Start both services
./scripts/dev.sh
```

This will:
- Start backend API on port 3401
- Start frontend dev server on port 3400
- Enable hot reload for both services
- Create logs in `logs/` directory

### Manual Development Setup

#### Backend

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start backend API
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 3401 --reload
```

#### Frontend

```bash
# Install dependencies
cd web_ui
pnpm install

# Start dev server
pnpm dev
```

### Development with Docker

Use the development Docker Compose configuration:

```bash
# Start backend in Docker with hot reload
./scripts/docker-up.sh --dev

# Frontend should still run locally
cd web_ui
pnpm dev
```

## Docker Deployment

### Production Deployment

```bash
# 1. Build images
./scripts/build.sh

# 2. Configure environment
cp .env.docker .env
# Edit .env with your configuration

# 3. Start services
./scripts/docker-up.sh

# 4. Check status
docker-compose ps

# 5. View logs
docker-compose logs -f
```

### Stop Services

```bash
# Stop services (keep data)
./scripts/docker-down.sh

# Stop and remove volumes
./scripts/docker-down.sh --volumes
```

### Build Options

```bash
# Build both images
./scripts/build.sh

# Build only backend
./scripts/build.sh --backend-only

# Build only frontend
./scripts/build.sh --frontend-only

# Build without cache
./scripts/build.sh --no-cache
```

## Production Deployment

### Docker Compose (Recommended)

The simplest production deployment uses Docker Compose:

```bash
# 1. Prepare environment
cp .env.docker .env
# Configure production values

# 2. Build images
./scripts/build.sh

# 3. Start in detached mode
docker-compose up -d

# 4. Monitor
docker-compose logs -f
```

### Reverse Proxy Setup (Nginx)

For production, use a reverse proxy:

```nginx
# /etc/nginx/sites-available/hypergraphrag
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:3401;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 60s;
    }
}
```

### SSL/TLS Configuration

Use Let's Encrypt for SSL:

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
```

### Kubernetes Deployment (Advanced)

For large-scale deployments, see `k8s/` directory (to be created).

## Environment Variables

### Backend (.env)

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-...                    # Required
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# Application
WORKING_DIR=/data/hypergraphrag           # Data directory
LOG_LEVEL=INFO                            # DEBUG, INFO, WARNING, ERROR

# CORS
CORS_ORIGINS=http://localhost:3400,http://localhost:80
```

### Frontend (web_ui/.env)

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:3401
```

## Testing

### Run All Tests

```bash
./scripts/test.sh
```

### Backend Tests Only

```bash
./scripts/test.sh --backend-only

# Or manually
python3 -m pytest tests/ -v
```

### Frontend Tests Only

```bash
./scripts/test.sh --frontend-only

# Or manually
cd web_ui
pnpm test --run
```

## Monitoring

### Health Checks

```bash
# Backend health
curl http://localhost:3401/api/health

# Frontend health
curl http://localhost:80/health
```

### Logs

```bash
# Docker logs
docker-compose logs -f

# Backend logs only
docker-compose logs -f backend

# Frontend logs only
docker-compose logs -f frontend

# Local development logs
tail -f logs/backend.log
tail -f logs/frontend.log
```

### Resource Usage

```bash
# Docker stats
docker stats

# Container details
docker-compose ps
```

## Troubleshooting

### Backend Won't Start

1. Check logs:
   ```bash
   docker-compose logs backend
   ```

2. Verify environment variables:
   ```bash
   docker-compose config
   ```

3. Check data directory:
   ```bash
   ls -la expr/example/
   ```

### Frontend Build Fails

1. Clear node_modules:
   ```bash
   cd web_ui
   rm -rf node_modules pnpm-lock.yaml
   pnpm install
   ```

2. Check Node version:
   ```bash
   node --version  # Should be 20+
   ```

### API Connection Issues

1. Check CORS configuration in `.env`
2. Verify backend is running:
   ```bash
   curl http://localhost:3401/api/health
   ```
3. Check frontend API URL in `web_ui/.env`

### Docker Issues

1. Clean up Docker:
   ```bash
   docker system prune -a
   ```

2. Rebuild images:
   ```bash
   ./scripts/build.sh --no-cache
   ```

3. Check Docker resources:
   ```bash
   docker info
   ```

### Port Conflicts

If ports are already in use:

```bash
# Check what's using the port
lsof -i :3401  # Backend
lsof -i :80    # Frontend

# Change ports in docker-compose.yml
# Backend: "8080:3401"
# Frontend: "8081:80"
```

## Performance Tuning

### Backend

- Increase worker processes in production
- Enable response caching
- Use connection pooling

### Frontend

- Enable gzip compression (already configured in nginx.conf)
- Use CDN for static assets
- Implement lazy loading for large graphs

### Docker

- Allocate more resources:
  ```yaml
  services:
    backend:
      deploy:
        resources:
          limits:
            cpus: '2'
            memory: 4G
  ```

## Security Checklist

- [ ] Change default ports in production
- [ ] Use strong API keys
- [ ] Enable HTTPS/SSL
- [ ] Configure firewall rules
- [ ] Limit CORS origins
- [ ] Enable rate limiting
- [ ] Regular security updates
- [ ] Monitor logs for suspicious activity

## Backup and Recovery

### Backup Data

```bash
# Backup hypergraph data
tar -czf backup-$(date +%Y%m%d).tar.gz expr/example/

# Backup logs
tar -czf logs-$(date +%Y%m%d).tar.gz logs/
```

### Restore Data

```bash
# Extract backup
tar -xzf backup-20241022.tar.gz

# Restart services
docker-compose restart
```

## Scaling

### Horizontal Scaling

Use Docker Swarm or Kubernetes for multiple replicas:

```bash
# Docker Swarm
docker service scale hypergraphrag-api=3
```

### Vertical Scaling

Increase container resources in `docker-compose.yml`.

## Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Documentation: `docs/`
- API Docs: http://localhost:3401/docs
