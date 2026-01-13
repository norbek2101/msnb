# Mini Social Network Backend

A REST API backend for a mini social network featuring users, posts, comments, likes, JWT authentication, and email verification.

## Features

- **User Management**: Registration, login, profile updates
- **JWT Authentication**: Secure token-based authentication with rate limiting
- **Email Verification**: Token-based email verification with expiration
- **Posts**: Create, read, update, delete posts with pagination and search
- **Comments**: Add and delete comments on posts
- **Likes**: Like/unlike posts (can't like your own post)
- **Feed Endpoint**: Get all users with their posts and likes
- **Admin Cleanup**: Remove unverified users after configurable time

## Tech Stack

- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy 2.0 (async)
- **Task Queue**: Celery + Redis
- **Authentication**: JWT (PyJWT)
- **Email**: FastAPI-Mail
- **Rate Limiting**: SlowAPI

## Quick Start

### Using Docker Compose

```bash
# Clone the repository
git clone <repository-url>
cd msnb

# Copy environment file
cp .env.example .env

# Start all services
docker compose up --build
```

The API will be available at `http://localhost:8000`

### API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Login and get JWT token |
| GET | `/auth/me` | Get current user profile |
| GET | `/auth/verify-email?token=...` | Verify email with token |
| POST | `/auth/resend-verification` | Resend verification email |

### Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| PATCH | `/users/me` | Update current user profile |

### Posts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/posts` | List posts (with pagination, search, date filter) |
| POST | `/posts` | Create a post (verified users only) |
| GET | `/posts/{id}` | Get post with comments |
| PATCH | `/posts/{id}` | Update post (author only) |
| DELETE | `/posts/{id}` | Delete post (author only) |

### Comments

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/posts/{id}/comments` | List comments on a post |
| POST | `/posts/{id}/comments` | Add comment (verified users only) |
| DELETE | `/posts/{post_id}/comments/{comment_id}` | Delete comment (author only) |

### Likes

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/posts/{id}/like` | Like a post |
| DELETE | `/posts/{id}/like` | Unlike a post |

### Feed

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/all` | Get all users with their posts and likes |

### Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/admin/cleanup-unverified` | Delete unverified users older than N hours |

## Example Requests

### Register

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "johndoe",
    "full_name": "John Doe",
    "password": "securepassword"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -d "username=user@example.com&password=securepassword"
```

### Create Post (with token)

```bash
curl -X POST http://localhost:8000/posts \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Post",
    "content": "This is the content of my first post."
  }'
```

### Get Posts with Pagination and Search

```bash
curl "http://localhost:8000/posts?page=1&page_size=10&search=hello"
```

## Project Structure

```
msnb/
├── alembic/                  # Database migrations
│   └── versions/
├── app/
│   ├── core/                 # Core functionality
│   │   ├── config.py         # Settings management
│   │   ├── security.py       # JWT and password hashing
│   │   ├── celery_app.py     # Celery configuration
│   │   ├── email.py          # Email sending
│   │   └── limiter.py        # Rate limiting
│   ├── repositories/         # Data access layer
│   │   ├── user_repository.py
│   │   ├── post_repository.py
│   │   ├── comment_repository.py
│   │   └── like_repository.py
│   ├── routers/              # API endpoints
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── posts.py
│   │   ├── feed.py
│   │   └── admin.py
│   ├── services/             # Business logic
│   │   ├── auth_service.py
│   │   ├── post_service.py
│   │   ├── comment_service.py
│   │   └── like_service.py
│   ├── database.py           # Database connection
│   ├── dependencies.py       # FastAPI dependencies
│   ├── main.py               # Application entry point
│   ├── models.py             # SQLAlchemy models
│   ├── schemas.py            # Pydantic schemas
│   └── tasks.py              # Celery tasks
├── scripts/
│   └── cleanup_unverified.py # Cleanup script
├── tests/                    # Test suite
├── docker-compose.yaml
├── Dockerfile
└── README.md
```

## Access Control Rules

- **Unverified users** (`is_verified = false`):
  - Can login and view posts
  - Can like posts
  - Cannot create posts or comments

- **Verified users**:
  - Can create/edit/delete their own posts
  - Can create/delete their own comments

## Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run all tests (quiet mode)
uv run pytest tests/ -q

# Run a specific test file
uv run pytest tests/test_auth.py -v

# Run tests with short traceback
uv run pytest tests/ -v --tb=short

# Run a single test
uv run pytest tests/test_auth.py::TestLogin::test_login_with_email_success -v
```

## Cleanup Script

To manually clean up unverified users:

```bash
# Default: 48 hours
python scripts/cleanup_unverified.py

# Custom hours
python scripts/cleanup_unverified.py --hours 24
```

Or use the admin endpoint:

```bash
curl -X POST "http://localhost:8000/admin/cleanup-unverified?hours=24"
```

## Environment Variables

See `.env.example` for all available configuration options.

## License

MIT
