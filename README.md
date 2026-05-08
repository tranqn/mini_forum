# MiniForum

A small forum-style API built with Django and Django REST Framework. Users can register, log in via token, and create posts and comments. Write endpoints are rate-limited so the same client cannot spam new posts or comments.

## Tech Stack

- Python 3.11+
- Django 6.0
- Django REST Framework 3.17
- Token Authentication
- SQLite (development)

## Getting Started

### 1. Clone the repository

```bash
git clone git@github.com:tranqn/mini_forum.git
cd mini_forum
```

### 2. Set up the virtual environment

```bash
python -m venv env
source env/bin/activate    # macOS/Linux
# env\Scripts\activate     # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply migrations

```bash
python manage.py migrate
```

### 5. Create a superuser (optional)

```bash
python manage.py createsuperuser
```

### 6. Run the development server

```bash
python manage.py runserver
```

API available at `http://127.0.0.1:8000/`.

## Project Structure

```
mini_forum/
├── core/               # Django project (settings, urls, wsgi, asgi)
├── user_auth_app/      # Registration + token login
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── forum_app/          # Posts and comments
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── permissions.py  # IsOwnerOrReadOnly
│   ├── throttling.py   # PostThrottle (POST-only, 1/min)
│   └── urls.py
├── manage.py
└── requirements.txt
```

## API Endpoints

### Authentication (no token required)

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| POST | `/auth/register/` | Register a new user | 201 |
| POST | `/auth/login/` | Obtain auth token | 200 |

### Posts (token required for write actions)

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| GET | `/api/posts/` | List all posts | 200 |
| POST | `/api/posts/` | Create a post | 201 |
| GET | `/api/posts/<id>/` | Retrieve a post | 200 |
| PUT/PATCH | `/api/posts/<id>/` | Update own post | 200 |
| DELETE | `/api/posts/<id>/` | Delete own post | 204 |

### Comments (token required for write actions)

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| GET | `/api/comments/` | List all comments | 200 |
| POST | `/api/comments/` | Create a comment | 201 |
| GET | `/api/comments/<id>/` | Retrieve a comment | 200 |
| PUT/PATCH | `/api/comments/<id>/` | Update own comment | 200 |
| DELETE | `/api/comments/<id>/` | Delete own comment | 204 |

Read access is open to anyone; modifying or deleting requires the resource owner's token.

## Domain Model

### Post

| Field | Type |
|-------|------|
| `title` | `CharField(max_length=200)` |
| `content` | `TextField` |
| `author` | `ForeignKey(User)` |
| `created_at` | `DateTimeField(auto_now_add=True)` |

### Comment

| Field | Type |
|-------|------|
| `post` | `ForeignKey(Post, related_name='comments')` |
| `text` | `TextField` |
| `author` | `ForeignKey(User)` |
| `created_at` | `DateTimeField(auto_now_add=True)` |

## Authentication

Register a user, then exchange username/password for a token:

```bash
curl -X POST http://127.0.0.1:8000/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"StrongPass1!","repeated_password":"StrongPass1!"}'

curl -X POST http://127.0.0.1:8000/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"StrongPass1!"}'
# → {"token": "abc123..."}
```

Then send the token with every authenticated request:

```bash
curl -H "Authorization: Token abc123..." http://127.0.0.1:8000/api/posts/
```

## Throttling

DRF rate limits are enabled globally:

| Scope | Limit |
|-------|-------|
| `anon` (unauthenticated, by IP) | 100 / hour |
| `user` (authenticated, by user) | 1000 / hour |
| `posts` (custom scope, POST only) | 1 / minute |

`forum_app/throttling.py` defines `PostThrottle`, a `ScopedRateThrottle` subclass that overrides `allow_request()` so the `posts` limit applies **only to POST requests**. GETs on the same endpoints fall back to the default `user`/`anon` limits.

The `PostThrottle` is wired into `PostListCreateView` and `CommentListCreateView`. Posts and comments share the same `posts` bucket per user — exceeding the limit returns `429 Too Many Requests` with a `Retry-After` header.

Quick test with two POSTs in a row:

```bash
curl -X POST http://127.0.0.1:8000/api/posts/ \
  -H "Authorization: Token abc123..." \
  -H "Content-Type: application/json" \
  -d '{"title":"Hello","content":"World"}'
# → 201 Created

curl -X POST http://127.0.0.1:8000/api/posts/ \
  -H "Authorization: Token abc123..." \
  -H "Content-Type: application/json" \
  -d '{"title":"Spam","content":"Spam"}'
# → 429 Too Many Requests
```

## Permissions

`IsOwnerOrReadOnly` (`forum_app/permissions.py`) lets anyone read posts and comments, but only the original author (or staff) may update or delete them.

## Notes

- `db.sqlite3` and `env/` are not committed.
- The default DRF throttle cache is in-memory; behind multiple workers (Gunicorn, multiple pods) configure a shared cache backend such as Redis to enforce limits consistently.
