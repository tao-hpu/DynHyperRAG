# HyperGraphRAG Scripts

This directory contains utility scripts for development, testing, and deployment.

## Available Scripts

### Development

#### `dev.sh` - Start Development Environment

Starts both backend and frontend in development mode with hot reload.

```bash
./scripts/dev.sh
```

**What it does:**
- Checks and installs dependencies
- Starts backend API on port 3401
- Starts frontend dev server on port 3400
- Creates logs in `logs/` directory
- Press Ctrl+C to stop all services

**Requirements:**
- Python 3.10+
- Node.js 20+ and pnpm
- `.env` file configured

---

### Docker Deployment

#### `docker-up.sh` - Start Docker Services

Starts the application using Docker Compose.

```bash
# Production mode
./scripts/docker-up.sh

# Development mode (with hot reload)
./scripts/docker-up.sh --dev

# Run in foreground (see logs)
./scripts/docker-up.sh --foreground

# Build images first
./scripts/docker-up.sh --build
```

**Options:**
- `--dev`: Use development configuration
- `--foreground` / `-f`: Run in foreground (don't detach)
- `--build`: Build images before starting

#### `docker-down.sh` - Stop Docker Services

Stops and removes Docker containers.

```bash
# Stop services (keep data)
./scripts/docker-down.sh

# Stop and remove volumes
./scripts/docker-down.sh --volumes
```

**Options:**
- `--volumes` / `-v`: Remove volumes (deletes data)

---

### Building

#### `build.sh` - Build Docker Images

Builds Docker images for production deployment.

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

**Options:**
- `--backend-only`: Build only backend image
- `--frontend-only`: Build only frontend image
- `--no-cache`: Build without using cache

**Output:**
- `hypergraphrag-api:latest`
- `hypergraphrag-web:latest`

---

### Testing

#### `test.sh` - Run Tests

Runs all tests for backend and frontend.

```bash
# Run all tests
./scripts/test.sh

# Backend tests only
./scripts/test.sh --backend-only

# Frontend tests only
./scripts/test.sh --frontend-only

# Verbose output
./scripts/test.sh --verbose
```

**Options:**
- `--backend-only`: Run only backend tests
- `--frontend-only`: Run only frontend tests
- `--verbose` / `-v`: Show detailed output

---

## Quick Start Guide

### First Time Setup

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Edit .env and add your OpenAI API key
nano .env

# 3. Start development environment
./scripts/dev.sh
```

### Docker Deployment

```bash
# 1. Copy Docker environment file
cp .env.docker .env

# 2. Edit .env and add your OpenAI API key
nano .env

# 3. Build and start
./scripts/docker-up.sh --build
```

### Running Tests

```bash
# Run all tests
./scripts/test.sh

# Or run specific tests
./scripts/test.sh --backend-only
```

---

## Script Permissions

All scripts should be executable. If not, run:

```bash
chmod +x scripts/*.sh
```

---

## Troubleshooting

### "Permission denied" error

Make scripts executable:
```bash
chmod +x scripts/*.sh
```

### "Command not found: pnpm"

Install pnpm:
```bash
npm install -g pnpm
```

### "Docker is not running"

Start Docker Desktop or Docker daemon:
```bash
# macOS
open -a Docker

# Linux
sudo systemctl start docker
```

### Port already in use

Check what's using the port:
```bash
lsof -i :3401  # Backend
lsof -i :3400  # Frontend dev
lsof -i :80    # Frontend production
```

Kill the process or change ports in configuration files.

---

## Environment Files

### `.env` - Main Configuration

Used by both local development and Docker deployment.

```bash
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
LOG_LEVEL=INFO
```

### `.env.docker` - Docker Template

Template for Docker deployment. Copy to `.env` and configure.

---

## Logs

### Local Development

Logs are written to:
- `logs/backend.log` - Backend API logs
- `logs/frontend.log` - Frontend dev server logs

View logs:
```bash
tail -f logs/backend.log
tail -f logs/frontend.log
```

### Docker Deployment

View Docker logs:
```bash
docker-compose logs -f
docker-compose logs -f backend
docker-compose logs -f frontend
```

---

## Additional Resources

- [DEPLOYMENT.md](../DEPLOYMENT.md) - Comprehensive deployment guide
- [README.md](../README.md) - Project overview
- [API Documentation](http://localhost:3401/docs) - When backend is running

---

## Support

For issues and questions:
- Check logs first
- Review [DEPLOYMENT.md](../DEPLOYMENT.md)
- Open an issue on GitHub
