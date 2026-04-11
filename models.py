import os

from dotenv import load_dotenv
import psycopg2
from psycopg2 import Error as PsycopgError
from psycopg2.extras import RealDictCursor
from psycopg2 import pool as pg_pool


load_dotenv()


class _PooledRepository:
    def __init__(self, conn_pool):
        self._pool = conn_pool

    def _run_read(self, operation):
        conn = None
        try:
            conn = self._pool.getconn()
            return operation(conn)
        except PsycopgError:
            if conn is not None and not conn.closed:
                conn.rollback()
            raise
        finally:
            if conn is not None:
                self._pool.putconn(conn)

    def _run_write(self, operation):
        conn = None
        try:
            conn = self._pool.getconn()
            result = operation(conn)
            conn.commit()
            return result
        except PsycopgError:
            if conn is not None and not conn.closed:
                conn.rollback()
            raise
        finally:
            if conn is not None:
                self._pool.putconn(conn)


class PostgresUserRepository(_PooledRepository):
    def __init__(self, conn_pool):
        super().__init__(conn_pool)
        self._ensure_schema()

    def _ensure_schema(self):
        def operation(conn):
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    """
                )

        self._run_write(operation)

    def save(self, user_data):
        def operation(conn):
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    INSERT INTO users (email, username, password)
                    VALUES (%s, %s, %s)
                    RETURNING id, email, username, password;
                    """,
                    (user_data["email"], user_data["username"], user_data["password"]),
                )
                return cursor.fetchone()

        return self._run_write(operation)

    def find_user_by_username(self, username):
        def operation(conn):
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT id, email, username, password FROM users WHERE username = %s;",
                    (username,),
                )
                return cursor.fetchone()

        return self._run_read(operation)

    def find_user_by_id(self, user_id):
        def operation(conn):
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT id, email, username, password FROM users WHERE id = %s;",
                    (user_id,),
                )
                return cursor.fetchone()

        return self._run_read(operation)

    def find_user_by_email(self, email):
        def operation(conn):
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT id, email, username, password FROM users WHERE email = %s;",
                    (email,),
                )
                return cursor.fetchone()

        return self._run_read(operation)

    def all_users(self):
        def operation(conn):
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT id, email, username FROM users;")
                return cursor.fetchall()

        return self._run_read(operation)


class PostgresNotesRepository(_PooledRepository):
    def __init__(self, conn_pool):
        super().__init__(conn_pool)
        self._ensure_schema()
        self._notes = []

    def _ensure_schema(self):
        def operation(conn):
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS notes (
                        id SERIAL PRIMARY KEY,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        user_id  INTEGER REFERENCES users(id),
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        updated_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    """
                )

        self._run_write(operation)

    def save_notes(self, note_data):
        def operation(conn):
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    INSERT INTO notes (title, content, user_id)
                    VALUES (%s, %s, %s)
                    RETURNING id, title, content, user_id, created_at, updated_at;
                    """,
                    (note_data["title"], note_data["content"], note_data["user_id"]),
                )
                return cursor.fetchone()

        saved_note = self._run_write(operation)
        self._notes.append(saved_note)
        return saved_note

    def find_notes_by_user_id(self, id):
        def operation(conn):
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT id, title, content, user_id, created_at, updated_at FROM notes WHERE user_id = %s ORDER BY id DESC;",
                    (id,),
                )
                return cursor.fetchall()

        notes = self._run_read(operation)
        self._notes = notes
        return notes

    def update_note(self, note_data):
        def operation(conn):
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    UPDATE notes
                    SET title = %s, content = %s, updated_at = NOW()
                    WHERE id = %s AND user_id = %s
                    RETURNING id, title, content, user_id, created_at, updated_at;
                    """,
                    (note_data["title"], note_data["content"], note_data["id"], note_data["user_id"]),
                )
                return cursor.fetchone()

        return self._run_write(operation)

    def delete_note(self, note_id, user_id):
        def operation(conn):
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    DELETE FROM notes
                    WHERE id = %s AND user_id = %s
                    RETURNING id;
                    """,
                    (note_id, user_id),
                )
                deleted_note = cursor.fetchone()
            return bool(deleted_note)

        return self._run_write(operation)

    def bulk_delete_notes(self, notes_ids, user_id):
        def operation(conn):
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    DELETE FROM notes
                    WHERE id = ANY(%s) and user_id = %s
                    RETURNING id;
                    """,
                    (notes_ids, user_id)
                )
                deleted_notes = cursor.fetchall()
            return [note["id"] for note in deleted_notes]

        return self._run_write(operation)


class PostgresTaskRepository(_PooledRepository):
    def __init__(self, conn_pool):
        super().__init__(conn_pool)
        self._ensure_schema()

    def _ensure_schema(self):
        def operation(conn):
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tasks (
                        id SERIAL PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT,
                        status TEXT NOT NULL DEFAULT 'pending',
                        due_date DATE,
                        user_id INTEGER REFERENCES users(id),
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        updated_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    """
                )

        self._run_write(operation)

    def save_task(self, task_data):
        def operation(conn):
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    INSERT INTO tasks (title, description, status, due_date, user_id)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, title, description, status, due_date, user_id, created_at, updated_at;
                    """,
                    (
                        task_data["title"],
                        task_data.get("description"),
                        task_data.get("status", "pending"),
                        task_data.get("due_date"),
                        task_data["user_id"],
                    ),
                )
                return cursor.fetchone()

        return self._run_write(operation)

    def find_tasks_by_user_id(self, user_id):
        def operation(conn):
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT id, title, description, status, due_date, user_id, created_at, updated_at FROM tasks WHERE user_id = %s ORDER BY id DESC;",
                    (user_id,),
                )
                return cursor.fetchall()

        return self._run_read(operation)

    def update_task(self, task_data):
        def operation(conn):
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    UPDATE tasks
                    SET title = %s, description = %s, status = %s, due_date = %s, updated_at = NOW()
                    WHERE id = %s AND user_id = %s
                    RETURNING id, title, description, status, due_date, user_id, created_at, updated_at;
                    """,
                    (
                        task_data["title"],
                        task_data.get("description"),
                        task_data.get("status", "pending"),
                        task_data.get("due_date"),
                        task_data["id"],
                        task_data["user_id"],
                    ),
                )
                return cursor.fetchone()

        return self._run_write(operation)

    def delete_task(self, task_id, user_id):
        def operation(conn):
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    DELETE FROM tasks
                    WHERE id = %s AND user_id = %s
                    RETURNING id;
                    """,
                    (task_id, user_id),
                )
                deleted_task = cursor.fetchone()
            return bool(deleted_task)

        return self._run_write(operation)

    def find_task_by_id(self, task_id, user_id):
        def operation(conn):
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT id, title, description, status, due_date, user_id, created_at, updated_at
                    FROM tasks
                    WHERE id = %s AND user_id = %s;
                    """,
                    (task_id, user_id),
                )
                return cursor.fetchone()

        return self._run_read(operation)

    def bulk_delete_tasks(self, task_ids, user_id):
        def operation(conn):
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    DELETE FROM tasks
                    WHERE id = ANY(%s) AND user_id = %s
                    RETURNING id;
                    """,
                    (task_ids, user_id),
                )
                deleted_tasks = cursor.fetchall()
            return [task["id"] for task in deleted_tasks]

        return self._run_write(operation)

    def find_tasks_by_status(self, user_id, status):
        def operation(conn):
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT id, title, description, status, due_date, user_id, created_at, updated_at
                    FROM tasks
                    WHERE user_id = %s AND status = %s
                    ORDER BY id DESC;
                    """,
                    (user_id, status),
                )
                return cursor.fetchall()

        return self._run_read(operation)


class InMemoryUserRepository:
    def __init__(self):
        self._users = []
        self._notes = []

    def save(self, user_data):
        self._users.append(user_data)
        return user_data

    def find_user_by_username(self, username):
        return next((u for u in self._users if u.get("username") == username), None)

    def find_user_by_id(self, user_id):
        return next((u for u in self._users if u.get("id") == user_id), None)

    def find_user_by_email(self, email):
        return next((u for u in self._users if u.get("email") == email), None)

    def all_users(self):
        return self._users
    
    
class InMemoryNotesRepository:
    def __init__(self):
        self._notes = []

    def save_notes(self, note_data):
        next_id = len(self._notes) + 1
        note = {
            "id": next_id,
            "title": note_data["title"],
            "content": note_data["content"],
            "user_id": note_data["user_id"],
        }
        self._notes.append(note)
        return note
    def update_note(self, note_data):
        for note in self._notes:
            if note["id"] == note_data["id"] and note["user_id"] == note_data["user_id"]:
                note["title"] = note_data["title"]
                note["content"] = note_data["content"]
                return note
        return None
    def delete_note(self, note_id, user_id):
        for i, note in enumerate(self._notes):
            if note["id"] == note_id and note["user_id"] == user_id:
                del self._notes[i]
                return True
        return False
    def find_notes_by_user_id(self, user_id):
        return [note for note in self._notes if note.get("user_id") == user_id]
    
    def bulk_delete_notes(self, notes_ids, user_id):
        deleted_ids = []
        for note_id in notes_ids:
            for i, note in enumerate(self._notes):
                if note["id"] == note_id and note["user_id"] == user_id:
                    del self._notes[i]
                    deleted_ids.append(note_id)
                    break
        return deleted_ids
    
class InMemoryTaskRepository:
    def __init__(self):
        self._tasks = []

    def save_task(self, task_data):
        next_id = len(self._tasks) + 1
        task = {
            "id": next_id,
            "title": task_data["title"],
            "description": task_data.get("description"),
            "status": task_data.get("status", "pending"),
            "due_date": task_data.get("due_date"),
            "user_id": task_data["user_id"],
        }
        self._tasks.append(task)
        return task
    def find_tasks_by_user_id(self, user_id):
        return [task for task in self._tasks if task.get("user_id") == user_id]
    
    def find_task_by_id(self, task_id, user_id):
        return next((task for task in self._tasks if task.get("id") == task_id and task.get("user_id") == user_id), None)
    
    def update_task(self, task_data):
        for i, task in enumerate(self._tasks):
            if task["id"] == task_data["id"] and task["user_id"] == task_data["user_id"]:
                self._tasks[i] = {**task, **task_data}
                return self._tasks[i]
        return None
    
    def delete_task(self, task_id, user_id):
        for i, task in enumerate(self._tasks):
            if task["id"] == task_id and task["user_id"] == user_id:
                del self._tasks[i]
                return True
        return False
    
    def find_tasks_by_status(self, user_id, status):
        return [task for task in self._tasks if task.get("user_id") == user_id and task.get("status") == status]

    def bulk_delete_tasks(self, task_ids, user_id):
        deleted_ids = []
        for task_id in task_ids:
            for i, task in enumerate(self._tasks):
                if task["id"] == task_id and task["user_id"] == user_id:
                    del self._tasks[i]
                    deleted_ids.append(task_id)
                    break
        return deleted_ids


shared_pool = None


def close_shared_connection():
    global shared_pool
    if shared_pool is not None:
        shared_pool.closeall()
    shared_pool = None


database_uri = os.getenv("DATABASE_URI", "")
normalized_db_uri = database_uri.replace("postgres://", "postgresql://", 1)
if normalized_db_uri.startswith("postgresql://"):
    pool_min = int(os.getenv("DB_POOL_MIN", "1"))
    pool_max = int(os.getenv("DB_POOL_MAX", "10"))
    if pool_min < 1:
        pool_min = 1
    if pool_max < pool_min:
        pool_max = pool_min

    try:
        shared_pool = pg_pool.ThreadedConnectionPool(
            minconn=pool_min,
            maxconn=pool_max,
            dsn=normalized_db_uri,
            connect_timeout=5,
        )
        if shared_pool.closed:
            raise RuntimeError("Database connection pool failed to initialize")
    except PsycopgError as exc:
        raise RuntimeError("Failed to connect to PostgreSQL. Check DATABASE_URI and database availability.") from exc
    except ValueError as exc:
        raise RuntimeError("Invalid DB_POOL_MIN or DB_POOL_MAX. Both must be integers.") from exc

    user_repo = PostgresUserRepository(shared_pool)
    notes_repo = PostgresNotesRepository(shared_pool)
    tasks_repo = PostgresTaskRepository(shared_pool)

else:
    user_repo = InMemoryUserRepository()
    notes_repo = InMemoryNotesRepository()
    tasks_repo = InMemoryTaskRepository()
