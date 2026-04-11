# Notes API

A Flask-based REST API for user authentication, notes, and tasks.

## Features

- User signup and login with JWT authentication
- CRUD operations for notes
- CRUD operations for tasks
- Bulk delete for notes and tasks
- Health and user-info endpoints

## Tech Stack

- Flask
- PostgreSQL via psycopg2
- PyJWT
- python-dotenv

## Project Structure

```text
app.py
config.py
models.py
requirements.txt
routes/
  auth.py
  notes.py
  tasks.py
  other.py
utils/
  hash.py
  jwt_handler.py
```
## API
```bash
https://tasks-manager-30hc.onrender.com
```
## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file with the required environment variables.
4. Run the app:

```bash
python app.py
```

## Render Deployment

- Python runtime is pinned in `runtime.txt` to `python-3.10.14`.
- Install command: `pip install -r requirements.txt`
- Start command (from Procfile): `gunicorn app:app`

## Environment Variables

- `SECRET_KEY` - Flask/JWT secret key
- `DATABASE_URI` - PostgreSQL connection string, for example `postgresql://user:password@localhost:5432/notes_api`

## Authentication Flow

- `POST /api/signup` creates a new user
- `POST /api/login` returns a JWT token
- Protected routes require an `Authorization` header:

```http
Authorization: Bearer <your_token>
```

## Routes

### Auth

| Method | Route | Auth | Description | Body |
| --- | --- | --- | --- | --- |
| POST | `/api/signup` | No | Register a new user. Validates email format and password strength. | `email`, `username`, `password` |
| POST | `/api/login` | No | Authenticate with `email` or `username` plus password and receive a JWT token. | `email` or `username`, `password` |

### Health and User Info

| Method | Route | Auth | Description | Body |
| --- | --- | --- | --- | --- |
| GET | `/api/alive` | No | Simple health check endpoint. | None |
| GET | `/api/user_info` | Yes | Returns the authenticated user profile summary. | None |

### Notes

| Method | Route | Auth | Description | Body |
| --- | --- | --- | --- | --- |
| GET | `/api/notes` | Yes | List all notes for the authenticated user. | None |
| POST | `/api/notes` | Yes | Create a new note for the authenticated user. | `title`, `content` |
| PUT | `/api/notes/<int:note_id>` | Yes | Update an existing note owned by the authenticated user. | `title`, `content` |
| DELETE | `/api/notes/<int:note_id>` | Yes | Delete a single note owned by the authenticated user. | None |
| DELETE | `/api/notes/bulk` | Yes | Delete multiple notes by ID. | `note_ids` as a list |

### Tasks

| Method | Route | Auth | Description | Body |
| --- | --- | --- | --- | --- |
| GET | `/api/tasks` | Yes | List all tasks for the authenticated user. | None |
| GET | `/api/tasks/<int:task_id>` | Yes | Fetch a single task owned by the authenticated user. | None |
| POST | `/api/tasks` | Yes | Create a new task for the authenticated user. | `title`, `description`, optional `due_date` |
| PUT | `/api/tasks/<int:task_id>` | Yes | Update an existing task owned by the authenticated user. | `title`, `description`, optional `due_date`, optional `status` |
| DELETE | `/api/tasks/<int:task_id>` | Yes | Delete a single task owned by the authenticated user. | None |
| DELETE | `/api/tasks/bulk` | Yes | Delete multiple tasks by ID. | `task_ids` as a list |

## Ownership Model

- Authenticated routes use the `user_id` from the JWT token, not a client-supplied value.
- Notes and tasks are always filtered by the current user's `user_id`.
- Create, update, delete, and bulk operations are restricted to records owned by that `user_id`.
- The API never expects `user_id` in request bodies for protected note or task operations.

## Example Requests

### Create a note

```bash
curl -X POST http://localhost:5000/api/notes \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"title":"Meeting notes","content":"Discuss roadmap and launch steps"}'
```
