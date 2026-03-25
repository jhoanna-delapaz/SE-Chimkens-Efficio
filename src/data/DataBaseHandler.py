
import sqlite3
from sqlite3 import Error
from typing import Optional
from data.models import Task


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn


def _serialize_for_sqlite(value) -> str:
    """Convert datetime to ISO string for sqlite3 (avoids Python 3.12+ DeprecationWarning)."""
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value) if value else ""


def _row_to_task(row) -> Task:
    """Map a DB row to a Task. DB stores created_at/due_date as ISO strings."""
    return Task(
        id=row[0],
        title=row[1],
        description=row[2] or "",
        status=row[3],
        created_at=row[4],
        due_date=row[5] or "",
        priority=row[6],
        is_deleted=row[7] if len(row) > 7 else 0,
        color=row[8] if len(row) > 8 else "#333333"  # Parse color or fallback
    )


def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)


def init_db(db_file):
    """
    Initializes the database and safely auto-migrates old schemas
    to prevent application crashes on legacy databases.
    """
    database = db_file

    sql_create_tasks_table = """ CREATE TABLE IF NOT EXISTS tasks (
                                        id integer PRIMARY KEY,
                                        title text NOT NULL,
                                        description text,
                                        status text NOT NULL,
                                        created_at text NOT NULL,
                                        due_date text,
                                        priority text
                                    ); """

    sql_create_user_profile_table = """ CREATE TABLE IF NOT EXISTS user_profile (
                                        id integer PRIMARY KEY,
                                        name text NOT NULL,
                                        email text
                                    ); """

    # create a database connection
    conn = create_connection(database)

    # create tables
    if conn is not None:
        try:
            create_table(conn, sql_create_tasks_table)
            create_table(conn, sql_create_user_profile_table)

            # ISO 25010 Reliability: Safely attempt to migrate older databases
            try:
                cur = conn.cursor()
                cur.execute("ALTER TABLE tasks ADD COLUMN is_deleted integer DEFAULT 0")
                conn.commit()
                print("Database successfully migrated to Sprint 2 SCHEMA (Added is_deleted).")
            except Exception:
                pass

            # ISO 25010 Reliability: Safely migrate Color Feature
            try:
                cur = conn.cursor()
                cur.execute("ALTER TABLE tasks ADD COLUMN color TEXT DEFAULT '#FFFFFF'")
                conn.commit()
                print("Database successfully migrated to Color SCHEMA.")
            except Exception:
                pass

        finally:
            conn.close()
    else:
        print("Error! cannot create the database connection.")


class DataHandler:
    """
    DB abstraction layer. All task CRUD and SQL live here.
    Business logic (TaskManager) calls this; future components (e.g. Analytics) can too.
    """

    def __init__(self, db_file: str):
        self.db_file = db_file
        self._conn = create_connection(db_file)
        if self._conn is None:
            raise RuntimeError(f"Could not connect to database: {db_file}")

    def close(self) -> None:
        """Close the connection. Call on shutdown to avoid file locks."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def add_task(self, task: Task) -> int:
        cur = self._conn.cursor()
        cur.execute(
            """INSERT INTO tasks
               (title, description, status, created_at, due_date, priority, is_deleted, color)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                task.title,
                task.description or "",
                task.status,
                _serialize_for_sqlite(task.created_at),
                _serialize_for_sqlite(task.due_date),
                task.priority,
                0,  # Default to active when created
                task.color  # NEW
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def get_all_tasks(self, search_query: str = "") -> list:
        """Fetches ACTIVE tasks, optionally filtered by a search keyword."""
        cur = self._conn.cursor()

        if search_query:
            # Add wildcards to match the string anywhere inside the field
            query = f"%{search_query}%"
            cur.execute("""
                SELECT * FROM tasks
                WHERE (is_deleted = 0 OR is_deleted IS NULL)
                AND (title LIKE ? OR description LIKE ?)
            """, (query, query))
        else:
            cur.execute("SELECT * FROM tasks WHERE is_deleted = 0 OR is_deleted IS NULL")

        rows = cur.fetchall()
        return [_row_to_task(r) for r in rows]

    def get_deleted_tasks(self, search_query: str = "") -> list:
        """Fetches TRASH tasks, optionally filtered by a search keyword."""
        cur = self._conn.cursor()

        if search_query:
            query = f"%{search_query}%"
            cur.execute("""
                SELECT * FROM tasks
                WHERE is_deleted = 1
                AND (title LIKE ? OR description LIKE ?)
            """, (query, query))
        else:
            cur.execute("SELECT * FROM tasks WHERE is_deleted = 1")

        rows = cur.fetchall()
        return [_row_to_task(r) for r in rows]

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
        row = cur.fetchone()
        return _row_to_task(row) if row else None

    def delete_task(self, task_id: int) -> None:
        """Soft-deletes a task by moving it to the Trash."""
        cur = self._conn.cursor()
        cur.execute("UPDATE tasks SET is_deleted = 1 WHERE id=?", (task_id,))
        self._conn.commit()

    def update_task_status(self, task_id: int, status: str) -> None:
        cur = self._conn.cursor()
        cur.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
        self._conn.commit()

    def update_task(self, task: Task) -> None:
        cur = self._conn.cursor()
        cur.execute(
            """UPDATE tasks SET title=?, description=?, status=?
               , due_date=?, priority=?, color=? WHERE id=?""",
            (
                task.title,
                task.description or "",
                task.status,
                _serialize_for_sqlite(task.due_date),
                task.priority,
                task.color,
                task.id,
            ),
        )
        self._conn.commit()

    def restore_task(self, task_id: int) -> None:
        """Restores a task from the Trash back to the main dashboard."""
        cur = self._conn.cursor()
        cur.execute("UPDATE tasks SET is_deleted = 0 WHERE id=?", (task_id,))
        self._conn.commit()

    def permanently_delete_task(self, task_id: int) -> None:
        """Physically removes the task from system storage permanently."""
        cur = self._conn.cursor()
        cur.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self._conn.commit()
