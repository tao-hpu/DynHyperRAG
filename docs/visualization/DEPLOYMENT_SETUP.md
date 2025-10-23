# Deployment Setup Summary

This document summarizes the deployment infrastructure created for HyperGraphRAG Visualization.

## Overview

Task 19 "配置部署环境" has been completed with all three sub-tasks:
- ✅ 19.1 编写 Dockerfile
- ✅ 19.2 配置 Docker Compose
- ✅ 19.3 配置开发环境脚本

## Files Created

### Docker Configuration

#### Backend Dockerfile (`api/Dockerfile`)
- Multi-stage build for optimized image size
- Python 3.10-slim base image
- Installs dependencies in builder stage
- Production stage copies only necessary files
- Exposes port 3401
- Includes health check
- Final image size: ~200MB (estimated)

#### Frontend Dockerfile (`web_ui/Dockerfile`)
- Multi-stage build with Node.js 20-alpine
- Uses pnpm for package management
- Builds static assets with Vite
- Production stage uses Nginx Alpine
- Includes custom nginx configuration
- Exposes port 80
- Includes health check
- Final image size: ~50MB (estimated)

#### Nginx Configuration (`web_ui/nginx.conf`)
- Serves static assets with caching
- Proxies API requests to backend
- SPA fallback routing
- Gzip compression enabled
- Security headers configured
- Health check endpoint

#### Docker Ignore Files
- `api/.dockerignore` - Excludes Python cache, venv, logs
- `web_ui/.dockerignore` - Excludes node_modules, build artifacts

### Docker Compose

#### Production (`docker-compose.yml`)
- Backend service on port 3401
- Frontend service on port 80
- Environment variable configuration
- Volume mounts for data persistence
- Health checks for both services
- Network isolation
- Restart policies

#### Development (`docker-compose.dev.yml`)
- Backend with hot reload
- Source code volume mounts
- Debug logging enabled
- Simplified for development workflow

#### Environment Template (`.env.docker`)
- OpenAI API configuration
- Application settings
- CORS configuration
- Template for users to copy and configure

### Utility Scripts

All scripts are located in `scripts/` directory and are executable.

#### `dev.sh` - Development Environment
- Checks dependencies
- Starts backend API (port 3401)
- Starts frontend dev server (port 3400)
- Creates log files
- Handles graceful shutdown

#### `build.sh` - Build Docker Images
- Builds backend and/or frontend images
- Supports selective building
- Tags with version and 'latest'
- No-cache option available
- Shows build summary

#### `docker-up.sh` - Start Docker Services
- Starts production or development mode
- Builds images if requested
- Waits for health checks
- Shows service URLs
- Detached or foreground mode

#### `docker-down.sh` - Stop Docker Services
- Stops all services
- Optional volume removal
- Handles both prod and dev configs

#### `test.sh` - Run Tests
- Runs backend tests (pytest)
- Runs frontend tests (vitest)
- Selective test execution
- Verbose mode available

### Documentation

#### `DEPLOYMENT.md`
Comprehensive deployment guide covering:
- Quick start instructions
- Development setup
- Docker deployment
- Production deployment
- Environment variables
- Monitoring and logging
- Troubleshooting
- Security checklist
- Backup and recovery
- Scaling strategies

#### `scripts/README.md`
Quick reference for all scripts:
- Usage examples
- Available options
- Troubleshooting tips
- Environment configuration

### Additional Files

#### `logs/.gitkeep`
- Creates logs directory
- Preserves directory in git

#### Updated `.gitignore`
- Ignores Docker environment files
- Ignores log files
- Ignores backup archives

## Architecture

```
┌─────────────────────────────────────────┐
│         Docker Compose Network          │
│                                         │
│  ┌──────────────┐    ┌──────────────┐ │
│  │   Frontend   │    │   Backend    │ │
│  │  (Nginx)     │───▶│  (FastAPI)   │ │
│  │  Port 80     │    │  Port 3401   │ │
│  └──────────────┘    └──────────────┘ │
│         │                    │         │
└─────────┼────────────────────┼─────────┘
          │                    │
          ▼                    ▼
    Static Assets        Data Volume
    (Built with Vite)    (expr/example)
```

## Deployment Options

### 1. Local Development (Recommended for Development)
```bash
./scripts/dev.sh
```
- Fast iteration
- Hot reload
- Direct debugging
- No Docker overhead

### 2. Docker Development
```bash
./scripts/docker-up.sh --dev
```
- Containerized backend
- Local frontend development
- Closer to production

### 3. Docker Production
```bash
./scripts/docker-up.sh --build
```
- Full containerization
- Production-ready
- Easy deployment
- Scalable

## Port Configuration

| Service | Development | Production | Docker Internal |
|---------|-------------|------------|-----------------|
| Backend API | 3401 | 3401 | 3401 |
| Frontend Dev | 3400 | - | - |
| Frontend Prod | - | 80 | 80 |

## Environment Variables

### Required
- `OPENAI_API_KEY` - OpenAI API key for LLM and embeddings

### Optional
- `OPENAI_BASE_URL` - Custom OpenAI endpoint (default: official API)
- `LLM_MODEL` - LLM model name (default: gpt-4o-mini)
- `EMBEDDING_MODEL` - Embedding model (default: text-embedding-3-small)
- `LOG_LEVEL` - Logging level (default: INFO)
- `CORS_ORIGINS` - Allowed CORS origins

## Quick Start

### First Time Setup

1. **Copy environment file:**
   ```bash
   cp .env.docker .env
   ```

2. **Configure OpenAI API key:**
   ```bash
   nano .env  # Add your OPENAI_API_KEY
   ```

3. **Choose deployment method:**

   **Option A: Local Development**
   ```bash
   ./scripts/dev.sh
   ```

   **Option B: Docker**
   ```bash
   ./scripts/docker-up.sh --build
   ```

4. **Access the application:**
   - Frontend: http://localhost (Docker) or http://localhost:3400 (Local)
   - Backend API: http://localhost:3401
   - API Docs: http://localhost:3401/docs

## Testing

Run all tests:
```bash
./scripts/test.sh
```

Run specific tests:
```bash
./scripts/test.sh --backend-only
./scripts/test.sh --frontend-only
```

## Monitoring

### Health Checks

```bash
# Backend
curl http://localhost:3401/api/health

# Frontend
curl http://localhost:80/health
```

### Logs

**Local Development:**
```bash
tail -f logs/backend.log
tail -f logs/frontend.log
```

**Docker:**
```bash
docker-compose logs -f
docker-compose logs -f backend
docker-compose logs -f frontend
```

## Production Considerations

### Security
- [ ] Configure SSL/TLS certificates
- [ ] Set up reverse proxy (Nginx/Traefik)
- [ ] Enable rate limiting
- [ ] Restrict CORS origins
- [ ] Use secrets management
- [ ] Regular security updates

### Performance
- [ ] Enable response caching
- [ ] Configure CDN for static assets
- [ ] Optimize Docker image sizes
- [ ] Set resource limits
- [ ] Monitor resource usage

### Reliability
- [ ] Set up health monitoring
- [ ] Configure log aggregation
- [ ] Implement backup strategy
- [ ] Set up alerting
- [ ] Document recovery procedures

## Next Steps

1. **Test the deployment:**
   ```bash
   ./scripts/docker-up.sh --build
   ```

2. **Verify all services:**
   - Check health endpoints
   - Test API functionality
   - Verify frontend loads

3. **Review documentation:**
   - Read DEPLOYMENT.md for detailed guide
   - Check scripts/README.md for script usage

4. **Customize for your environment:**
   - Adjust ports if needed
   - Configure environment variables
   - Set up monitoring

## Troubleshooting

See [DEPLOYMENT.md](../../DEPLOYMENT.md) for comprehensive troubleshooting guide.

Common issues:
- Port conflicts: Change ports in docker-compose.yml
- Permission errors: Run `chmod +x scripts/*.sh`
- Docker not running: Start Docker Desktop
- Build failures: Try `./scripts/build.sh --no-cache`

## Support

- Documentation: `docs/` directory
- API Documentation: http://localhost:3401/docs (when running)
- Scripts Help: `scripts/README.md`
- Deployment Guide: `DEPLOYMENT.md`

---

**Status:** ✅ Task 19 Complete - All deployment infrastructure is ready for use.
