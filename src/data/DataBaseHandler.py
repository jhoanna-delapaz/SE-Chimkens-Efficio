
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
        create_table(conn, sql_create_tasks_table)
        create_table(conn, sql_create_user_profile_table)
        conn.close()
        print("Database initialized successfully.")
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
        sql = """INSERT INTO tasks(title, description, status, created_at, due_date, priority)
                 VALUES(?,?,?,?,?,?)"""
        cur = self._conn.cursor()
        cur.execute(sql, (
            task.title,
            task.description or "",
            task.status,
            _serialize_for_sqlite(task.created_at),
            _serialize_for_sqlite(task.due_date),
            task.priority,
        ))
        self._conn.commit()
        return cur.lastrowid

    def get_all_tasks(self) -> list:
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM tasks")
        return [_row_to_task(row) for row in cur.fetchall()]

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
        row = cur.fetchone()
        return _row_to_task(row) if row else None

    def delete_task(self, task_id: int) -> None:
        cur = self._conn.cursor()
        cur.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self._conn.commit()

    def update_task_status(self, task_id: int, status: str) -> None:
        cur = self._conn.cursor()
        cur.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
        self._conn.commit()

    def update_task(self, task: Task) -> None:
        cur = self._conn.cursor()
        cur.execute(
            """UPDATE tasks SET title=?, description=?, status=?, due_date=?, priority=? WHERE id=?""",
            (
                task.title,
                task.description or "",
                task.status,
                _serialize_for_sqlite(task.due_date),
                task.priority,
                task.id,
            ),
        )
        self._conn.commit()


