import os

from dotenv import load_dotenv
import psycopg2
from psycopg2 import Error as PsycopgError
from psycopg2.extras import RealDictCursor


load_dotenv()


class PostgresUserRepository:
    def __init__(self, conn):
        self._conn = conn
        self._ensure_schema()

    def _ensure_schema(self):
        with self._conn.cursor() as cursor:
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
        self._conn.commit()

    def save(self, user_data):
        try:
            with self._conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    INSERT INTO users (email, username, password)
                    VALUES (%s, %s, %s)
                    RETURNING id, email, username, password;
                    """,
                    (user_data["email"], user_data["username"], user_data["password"]),
                )
                user = cursor.fetchone()
            self._conn.commit()
            return user
        except PsycopgError:
            self._conn.rollback()
            raise
    

    def find_user_by_username(self, username):
        try:
            with self._conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT id, email, username, password FROM users WHERE username = %s;",
                    (username,),
                )
                return cursor.fetchone()
        except PsycopgError:
            self._conn.rollback()
            raise


    def find_user_by_id(self, user_id):
        try:
            with self._conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT id, email, username, password FROM users WHERE id = %s;",
                    (user_id,),
                )
                return cursor.fetchone()
        except PsycopgError:
            self._conn.rollback()
            raise

    def find_user_by_email(self, email):
        try:
            with self._conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT id, email, username, password FROM users WHERE email = %s;",
                    (email,),
                )
                return cursor.fetchone()
        except PsycopgError:
            self._conn.rollback()
            raise

    def all_users(self):
        try:
            with self._conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT id, email, username FROM users;")
                return cursor.fetchall()
        except PsycopgError:
            self._conn.rollback()
            raise

   
class PostgresNotesRepository:
    def __init__(self, conn):
        self._conn = conn
        self._ensure_schema()
        self._notes = []
    def _ensure_schema(self):
        with self._conn.cursor() as cursor:
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
        self._conn.commit()

    def save_notes(self, note_data):
        try:
            with self._conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    INSERT INTO notes (title, content, user_id)
                    VALUES (%s, %s, %s)
                    RETURNING id, title, content, user_id, created_at, updated_at;
                    """,
                    (note_data["title"], note_data["content"], note_data["user_id"]),
                )
                saved_note = cursor.fetchone()
            self._conn.commit()
        except PsycopgError:
            self._conn.rollback()
            raise
        self._notes.append(saved_note)
        return saved_note

    def find_notes_by_user_id(self, id):
        try:
            with self._conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT id, title, content, user_id, created_at, updated_at FROM notes WHERE user_id = %s ORDER BY id DESC;",
                    (id,),
                )
                notes = cursor.fetchall()
        except PsycopgError:
            self._conn.rollback()
            raise
        self._notes = notes
        return notes
    
    def update_note(self, note_data):
        try:
            with self._conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    UPDATE notes
                    SET title = %s, content = %s, updated_at = NOW()
                    WHERE id = %s AND user_id = %s
                    RETURNING id, title, content, user_id, created_at, updated_at;
                    """,
                    (note_data["title"], note_data["content"], note_data["id"], note_data["user_id"]),
                )
                updated_note = cursor.fetchone()
            self._conn.commit()
            return updated_note
        except PsycopgError:
            self._conn.rollback()
            raise

    def delete_note(self, note_id, user_id):
        try:
            with self._conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    DELETE FROM notes
                    WHERE id = %s AND user_id = %s
                    RETURNING id;
                    """,
                    (note_id, user_id),
                )
                deleted_note = cursor.fetchone()
            self._conn.commit()
            return bool(deleted_note)
        except PsycopgError:
            self._conn.rollback()
            raise
    
    def bulk_delete_notes(self, notes_ids, user_id):
        try:
            with self._conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    DELETE FROM notes
                    WHERE id = ANY(%s) and user_id = %s
                    RETURNING id;
                    """,
                    (notes_ids,user_id)
                )
                deleted_notes = cursor.fetchall()
            self._conn.commit()
            return [note["id"] for note in deleted_notes]
        except PsycopgError:
            self._conn.rollback()
            raise

class PostgresTaskRepository:
    def __init__(self, conn):
        self.__conn = conn
        self._ensure_schema()

    def _ensure_schema(self):
        with self.__conn.cursor(cursor_factory=RealDictCursor) as cursor:
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
        self.__conn.commit()

    def save_task(self, task_data):
        try:
            with self.__conn.cursor(cursor_factory=RealDictCursor) as cursor:
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
                task = cursor.fetchone()
            self.__conn.commit()
            return task
        except PsycopgError:
            self.__conn.rollback()
            raise
    
    def find_tasks_by_user_id(self, user_id):
        try:
            with self.__conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT id, title, description, status, due_date, user_id, created_at, updated_at FROM tasks WHERE user_id = %s ORDER BY id DESC;",
                    (user_id,),
                )
                return cursor.fetchall()
        except PsycopgError:
            self.__conn.rollback()
            raise
    
    def update_task(self, task_data):
        try:
            with self.__conn.cursor(cursor_factory=RealDictCursor) as cursor:
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
                updated_task = cursor.fetchone()
            self.__conn.commit()
            return updated_task
        except PsycopgError:
            self.__conn.rollback()
            raise
    
    def delete_task(self, task_id, user_id):
        try:
            with self.__conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    DELETE FROM tasks
                    WHERE id = %s AND user_id = %s
                    RETURNING id;
                    """,
                    (task_id, user_id),
                )
                deleted_task = cursor.fetchone()
            self.__conn.commit()
            return bool(deleted_task)
        except PsycopgError:
            self.__conn.rollback()
            raise
    
    def find_task_by_id(self, task_id, user_id):
        try:
            with self.__conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT id, title, description, status, due_date, user_id, created_at, updated_at
                    FROM tasks
                    WHERE id = %s AND user_id = %s;
                    """,
                    (task_id, user_id),
                )
                return cursor.fetchone()
        except PsycopgError:
            self.__conn.rollback()
            raise
    def bulk_delete_tasks(self,task_ids, user_id):
        try:
            with self.__conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    DELETE FROM tasks
                    WHERE id = ANY(%s) AND user_id = %s
                    RETURNING id;
                    """,
                    (task_ids, user_id),
                )
                deleted_tasks = cursor.fetchall()
            self.__conn.commit()
            return [task["id"] for task in deleted_tasks]
        except PsycopgError:
            self.__conn.rollback()
            raise
    
    def find_tasks_by_status(self, user_id, status):
        try:
            with self.__conn.cursor(cursor_factory=RealDictCursor) as cursor:
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
        except PsycopgError:
            self.__conn.rollback()
            raise
    
        
    


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


shared_conn = None


def close_shared_connection():
    global shared_conn
    if shared_conn is not None and not shared_conn.closed:
        shared_conn.close()
    shared_conn = None


database_uri = os.getenv("DATABASE_URI", "")
normalized_db_uri = database_uri.replace("postgres://", "postgresql://", 1)
if normalized_db_uri.startswith("postgresql://"):
    try:
        shared_conn = psycopg2.connect(normalized_db_uri, connect_timeout=5)
    except PsycopgError as exc:
        raise RuntimeError("Failed to connect to PostgreSQL. Check DATABASE_URI and database availability.") from exc
    shared_conn.autocommit = False
    user_repo = PostgresUserRepository(shared_conn)
    notes_repo = PostgresNotesRepository(shared_conn)
    tasks_repo = PostgresTaskRepository(shared_conn)

else:
    user_repo = InMemoryUserRepository()
    notes_repo = InMemoryNotesRepository()
    tasks_repo = InMemoryTaskRepository()
