# Docker & Docker Compose Guide

## Overview

This project includes a complete Docker setup with:

- **Multi-stage Dockerfile** for optimized production builds
- **Development Dockerfile** with hot reload
- **Production vs Development** compose files
- **Health checks** for all services
- **Nginx reverse proxy** with SSL support
- **Redis caching layer**
- **MongoDB database**
- **Non-root user** for security

## Quick Start

### Development Environment (with hot reload)

```bash
make dev
# or
docker-compose -f docker-compose.dev.yml up -d
```

- App available at: `http://localhost:8000`
- Includes auto-reload on code changes
- No reverse proxy

### Production Environment

```bash
make prod
# or
docker-compose up -d
```

- App available at: `http://localhost` (via Nginx)
- Optimized multi-stage build
- All health checks enabled

## Key Features

### 1. Multi-Stage Build (Production)

- **Stage 1 (Builder)**: Install dependencies including build tools
- **Stage 2 (Runtime)**: Lightweight runtime with only essential packages
- **Result**: ~50-60% smaller image size
- **User**: Runs as non-root user (UID 1000) for security

### 2. Health Checks

- **FastAPI App**: HTTP GET `/health` endpoint
- **MongoDB**: Native `mongosh` ping command
- **Redis**: `redis-cli ping` command
- **Nginx**: HTTP GET to `/`
- **Interval**: 10-30 seconds

### 3. Networking

- Isolated `fastapi_network` for secure inter-container communication
- No exposed internal ports between containers
- Only required ports exposed to host

### 4. Volume Management

- **Named volumes** for persistent data
- Separate volumes for dev (`mongo_data_dev`) and prod (`mongo_data`)
- Redis data persistence with AOF (Append Only File)

### 5. Environment Variables

- `.env` for environment-specific configuration
- `.env.example` as template
- Development and production have different defaults

## Usage

### Common Commands

```bash
# View help
make help

# Development
make dev              # Start dev environment
make dev-logs         # View dev logs
make dev-rebuild      # Rebuild dev containers
make dev-stop         # Stop dev environment
make app-shell-dev    # Shell into dev app

# Production
make up               # Start production
make rebuild          # Rebuild production
make down             # Stop production
make logs             # View production logs

# Database access
make db-shell         # MongoDB shell
make redis-shell      # Redis CLI

# Application
make shell            # Bash shell in app
make test             # Run pytest in container

# Cleanup
make clean            # Remove containers & volumes
make clean-all        # Force remove everything
```

### Service Access

**Development:**

- FastAPI: http://localhost:8000
- MongoDB: localhost:27017
- Redis: localhost:6379

**Production (via Nginx):**

- API: http://localhost/
- Direct to FastAPI: http://localhost:8001
- MongoDB: localhost:27017 (not exposed in prod)
- Redis: localhost:6379 (not exposed in prod)

## Docker Architecture

### Services Included

1. **MongoDB (7.0)**
   - Data storage for tasks and users
   - Health check via mongosh
   - Persistent volume

2. **Redis (7-Alpine)**
   - Caching layer
   - Session management
   - AOF persistence

3. **FastAPI App**
   - Custom Python 3.13-slim image
   - Multi-stage build (production)
   - Hot reload (development)
   - Non-root user execution

4. **Nginx (Alpine)**
   - Reverse proxy
   - Gzip compression
   - SSL/TLS support (template provided)
   - Load balancing Ready

## Building Images

### Development Build

```bash
docker build -f fastapi-learning/Dockerfile.dev -t fastapi:dev .
```

### Production Build

```bash
docker build -f fastapi-learning/Dockerfile -t fastapi:latest .
```

### Custom Build

```bash
docker-compose build --no-cache
```

## Environment Configuration

### .env File Structure

```env
# MongoDB
MONGO_URI=mongodb://mongo:27017
MONGO_DB=taskdb

# JWT
SECRET_KEY=your-production-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_MINUTES=10080

# Redis
REDIS_URL=redis://redis:6379/0

# Environment
ENVIRONMENT=production
DEBUG=false
```

**Important**:

- Change `SECRET_KEY` in production
- Never commit `.env` to version control
- Use `.env.example` as template

## Logs and Debugging

### View Service Logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs app
docker-compose logs mongo
docker-compose logs redis
docker-compose logs nginx

# Follow logs
docker-compose logs -f

# Last N lines
docker-compose logs --tail 100
```

### Container Health

```bash
# Check health status
docker-compose ps

# Detailed inspection
docker inspect fastapi_app | jq '.[0].State.Health'
```

## Production Recommendations

### 1. SSL/TLS Configuration

Uncomment the HTTPS section in `nginx.conf` and add:

```bash
mkdir ssl
# Add your cert.pem and key.pem files
```

### 2. Environment Variables

```bash
# Create production .env
cp .env.example .env
# Edit with production values
nano .env
```

### 3. Resource Limits

Add to `docker-compose.yml` services:

```yaml
deploy:
  resources:
    limits:
      cpus: "1"
      memory: 512M
    reservations:
      cpus: "0.5"
      memory: 256M
```

### 4. Restart Policies

Already configured: `restart: unless-stopped`

### 5. Monitoring

```bash
# CPU and memory usage
docker stats

# Log rotation (add to Dockerfile)
# LOGGING_DRIVER: json-file
# LOG_OPT_MAX_SIZE: "10m"
# LOG_OPT_MAX_FILE: "3"
```

## Troubleshooting

### Containers not starting?

```bash
# Check logs
docker-compose logs

# Rebuild with no cache
docker-compose build --no-cache
docker-compose up -d
```

### Port already in use?

```bash
# Find process using port
lsof -i :8000
# Kill process or change port in docker-compose.yml
```

### Health checks failing?

```bash
# Test service manually
docker-compose exec app curl http://localhost:8000/health
docker-compose exec mongo mongosh localhost:27017
docker-compose exec redis redis-cli ping
```

### Volume issues?

```bash
# List volumes
docker volume ls

# Remove unused volumes
docker volume prune

# Backup volume
docker run --rm -v mongo_data:/src -v $(pwd):/backup alpine tar czf /backup/mongo_backup.tar.gz /src
```

## Performance Tips

1. **Multi-stage builds**: Reduces image size ~60%
2. **Alpine images**: For lightweight services (Redis, Nginx)
3. **Layer caching**: Order Dockerfile commands to leverage cache
4. **Health checks**: Prevents routing to unhealthy containers
5. **Networking**: Use internal networks, don't expose unnecessary ports
6. **Volumes**: Named volumes are more efficient than bind mounts

## Security Considerations

✅ **Implemented:**

- Non-root user execution
- Health checks prevent traffic to failing services
- Isolated networks
- `.dockerignore` excludes sensitive files
- No secrets in Dockerfile or docker-compose

⚠️ **To Implement:**

- Add SSL/TLS certificates for HTTPS
- Use secret management for sensitive data
- Scan images for vulnerabilities
- Keep base images updated regularly
- Configure resource limits
- Set up log rotation

## Next Steps

1. Update `.env` with your values
2. Configure SSL certificates in `nginx.conf`
3. Add Redis integration to your FastAPI app
4. Set up monitoring and logging
5. Test with production load
