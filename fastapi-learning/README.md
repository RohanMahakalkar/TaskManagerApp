# FastAPI Task Manager

A minimal FastAPI + MongoDB + JWT application with:

- user signup/login (bcrypt password + JWT auth)
- task CRUD (create, list, update, delete)
- pagination + search on `GET /tasks`
- token refresh (`POST /token/refresh`)
- role check middleware (`require_roles`)
- timestamps: `created_at`, `updated_at`

## Files

- `main.py` - app entrypoint
- `auth.py` - auth routes + JWT tokens
- `tasks.py` - task routes with metadata
- `database.py` - MongoDB connection + collections
- `schemas.py` - pydantic models
- `tests/test_api.py` - integration tests
- `Dockerfile` + `docker-compose.yml`
- `.env` - environment overrides
- `start.sh` - startup script
- `Makefile` - easy commands

## Setup

```bash
cd /Users/rohanmahakalkar/Desktop/FastAPIPro1/fastapi-learning
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

### Local Development

```bash
./start.sh
```

or with Makefile:

```bash
make run
```

Then visit: http://127.0.0.1:8000

## Docker Setup

The application is fully containerized with Docker Compose, including MongoDB, Redis, and Nginx reverse proxy.

### Quick Start

**Production (with Nginx):**

```bash
docker-compose up -d
# API available at: http://localhost
```

**Development (with hot reload):**

```bash
docker-compose -f docker-compose.dev.yml up -d
# API available at: http://localhost:8000
```

### Services

| Service | Port   | Notes                    |
| ------- | ------ | ------------------------ |
| FastAPI | 8001   | Direct access (internal) |
| Nginx   | 80/443 | Reverse proxy (public)   |
| MongoDB | 27017  | Database                 |
| Redis   | 6379   | Caching layer            |

### Docker Commands

```bash
# Start production
docker-compose up -d

# Start development (auto-reload)
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down

# Clean up volumes
docker-compose down -v
```

### Makefile Commands

```bash
make prod           # Start production environment
make dev            # Start development environment
make build          # Build Docker images
make logs           # View all logs
make shell          # Access app shell
make db-shell       # MongoDB shell
make redis-shell    # Redis CLI
make test           # Run tests
make ps             # Show running containers
make help           # All available commands
```

### Environment Variables

Create a `.env` file in the root directory:

```env
MONGO_URI=mongodb://mongo:27017
MONGO_DB=taskdb
SECRET_KEY=your-secret-key-here
REDIS_URL=redis://redis:6379/0
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_MINUTES=10080
```

### Architecture

```
┌─────────────┐
│   Nginx     │ ← Port 80/443 (Reverse Proxy)
└──────┬──────┘
       │
┌──────▼───────┐
│   FastAPI    │ ← Port 8000
└──────┬───────┘
       │
  ┌────┴────┐
  │          │
┌─▼──┐    ┌─▼──┐
│ DB │    │Redis│
└────┘    └─────┘
```

### Features

- ✅ **Multi-stage Docker build** - Optimized image size (~50-60% smaller)
- ✅ **Health checks** - All services monitored
- ✅ **Non-root user** - Security best practice
- ✅ **Persistent volumes** - Data survives container restarts
- ✅ **Nginx caching** - Gzip compression, SSL-ready
- ✅ **Redis integration** - For fast task-list caching
- ✅ **Development/Production** - Separate compose files
- ✅ **Hot reload** - Development mode with auto-reload

### Redis Task Cache Behavior

- **What is cached**: `GET /tasks` responses are cached per user and query parameters.
  - Key template: `tasks:{user_id}:{page}:{limit}:{search}`
  - Value: JSON payload containing `page`, `limit`, `total`, `pages`, `search`, `items`
  - `items` is a list of tasks with `id`, `name`, `user_id`, `created_at`, `updated_at`

- **TTL**: configured via environment variable `REDIS_TTL_SECONDS` (default `60` seconds). Cached entries auto-expire after TTL.

- **Invalidation on write**:
  - `POST /tasks` (create) invalidates `tasks:{user_id}:*` keys.
  - `PUT /tasks/{task_id}` (update) invalidates `tasks:{user_id}:*` keys.
  - `DELETE /tasks/{task_id}` (delete) invalidates `tasks:{user_id}:*` keys.

This ensures stale task lists are refreshed after changes.

### Rate Limiting

- **Middleware**: `RateLimitMiddleware` in `rate_limit.py` is automatically added in `main.py`.
- **Configurable limit** via environment variable `RATE_LIMIT_PER_MINUTE` (default `60`).
- **Token bucket window**: 60 seconds.
- **Exceeding limit**: returns `429 Too Many Requests` with `Retry-After` header and body `{"detail": "Rate limit exceeded. Try again later."}`.
- Response headers include `X-RateLimit-Limit` and `X-RateLimit-Remaining`.

### Rate Limit Testing

In `tests/test_api.py`, there is a dedicated check:
- Set `RATE_LIMIT_PER_MINUTE=3` for isolated test behavior
- Ensure first `GET /tasks` is allowed and immediate next request triggers `429` response

### Access Services

**Inside Docker:**

```bash
# FastAPI
curl http://localhost/health

# Direct FastAPI
curl http://localhost:8001/health

# MongoDB
docker-compose exec mongo mongosh

# Redis
docker-compose exec redis redis-cli ping
```

For more details on Docker setup, see [DOCKER_GUIDE.md](../DOCKER_GUIDE.md)

## API examples

### Signup

```bash
curl -X POST http://127.0.0.1:8000/signup \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"secret"}'
```

### Login

```bash
curl -X POST http://127.0.0.1:8000/login \
  -d 'username=alice' -d 'password=secret'
```

### Create task

```bash
curl -X POST http://127.0.0.1:8000/tasks \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Buy milk"}'
```

### List tasks

```bash
curl -X GET 'http://127.0.0.1:8000/tasks?page=1&limit=5&search=milk' \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### Update task

```bash
curl -X PUT http://127.0.0.1:8000/tasks/<TASK_ID> \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Buy almond milk"}'
```

### Delete task

```bash
curl -X DELETE http://127.0.0.1:8000/tasks/<TASK_ID> \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### Refresh token

```bash
curl -X POST http://127.0.0.1:8000/token/refresh \
  -H 'Content-Type: application/json' \
  -d '{"refresh_token":"<REFRESH_TOKEN>"}'
```

## Docker

```bash
docker compose up --build
```

## Tests

```bash
make test
```

## Environment variables

`fastapi-learning/.env` covers defaults:

- `MONGO_URI`
- `MONGO_DB`
- `SECRET_KEY`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `REFRESH_TOKEN_EXPIRE_MINUTES`
