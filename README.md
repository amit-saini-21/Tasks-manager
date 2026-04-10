# Notes API

A Flask-based REST API for user authentication, notes, tasks, and AI-powered productivity suggestions.

## Features

- User signup and login with JWT authentication
- CRUD operations for notes
- CRUD operations for tasks
- Bulk delete for notes and tasks
- Health and user-info endpoints
- AI suggestions for general prompts, note improvement, and task planning

## Tech Stack

- Flask
- PostgreSQL via psycopg2
- PyJWT
- python-dotenv
- Google GenAI

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
  ai.py
utils/
  hash.py
  jwt_handler.py
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

## Environment Variables

- `SECRET_KEY` - Flask/JWT secret key
- `DATABASE_URI` - PostgreSQL connection string, for example `postgresql://user:password@localhost:5432/notes_api`
- `GEMINI_API_KEY` - Google Gemini API key used by the AI routes
- `GEMINI_MODEL` - Optional Gemini model name, defaults to `gemini-3-flash-preview`


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


## Example Requests

### Create a note

```bash
curl -X POST http://localhost:5000/api/notes \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"title":"Meeting notes","content":"Discuss roadmap and launch steps"}'
```

## Notes

- The AI routes require `GEMINI_API_KEY` in the environment.
- AI responses return a 429 status with guidance when the Gemini project quota is exhausted.
- The AI blueprint is registered in `app.py`, so all documented AI routes are active.
