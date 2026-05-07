import sqlite3
from sqlite3 import Error
from typing import Optional, List
from data.models import Task, Tag, TaskAttachment


def create_connection(db_file: str) -> Optional[sqlite3.Connection]:
    """create a database connection to the SQLite database
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


def _serialize_for_sqlite(value: any) -> str:
    """Convert datetime to ISO string for sqlite3 (avoids Python 3.12+ DeprecationWarning)."""
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value) if value else ""


def _row_to_task(row: tuple) -> Task:
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
        color=row[8] if len(row) > 8 else "#333333",  # Parse color or fallback
    )


def create_table(conn: sqlite3.Connection, create_table_sql: str) -> None:
    """create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)


def init_db(db_file: str) -> None:
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

    sql_create_tags_table = """ CREATE TABLE IF NOT EXISTS tags (
                                    id integer PRIMARY KEY,
                                    name text UNIQUE NOT NULL,
                                    color text DEFAULT '#333333'
                                ); """

    sql_create_task_tags_table = """ CREATE TABLE IF NOT EXISTS task_tags (
                                        task_id integer NOT NULL,
                                        tag_id integer NOT NULL,
                                        FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE,
                                        FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE,
                                        PRIMARY KEY (task_id, tag_id)
                                    ); """

    sql_create_attachments_table = """ CREATE TABLE IF NOT EXISTS task_attachments (
                                            id integer PRIMARY KEY,
                                            task_id integer NOT NULL,
                                            file_path text NOT NULL,
                                            file_name text NOT NULL,
                                            FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
                                        ); """

    # create a database connection
    conn = create_connection(database)

    # create tables
    if conn is not None:
        try:
            create_table(conn, sql_create_tasks_table)
            create_table(conn, sql_create_user_profile_table)
            create_table(conn, sql_create_tags_table)
            create_table(conn, sql_create_task_tags_table)
            create_table(conn, sql_create_attachments_table)

            # ISO 25010 Reliability: Safely attempt to migrate older databases
            try:
                cur = conn.cursor()
                cur.execute("ALTER TABLE tasks ADD COLUMN is_deleted integer DEFAULT 0")
                conn.commit()
                print(
                    "Database successfully migrated to Sprint 2 SCHEMA (Added is_deleted)."
                )
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

    def _attach_tags_to_tasks(self, tasks: List[Task]) -> List[Task]:
        if not tasks:
            return tasks

        task_ids = [t.id for t in tasks]
        placeholders = ",".join("?" * len(task_ids))

        cur = self._conn.cursor()
        cur.execute(
            f"""
            SELECT tt.task_id, t.id, t.name, t.color
            FROM task_tags tt
            JOIN tags t ON tt.tag_id = t.id
            WHERE tt.task_id IN ({placeholders})
        """,
            task_ids,
        )

        tags_by_task = {task_id: [] for task_id in task_ids}
        for row in cur.fetchall():
            task_id, tag_id, tag_name, tag_color = row
            tags_by_task[task_id].append(Tag(id=tag_id, name=tag_name, color=tag_color))

        for task in tasks:
            task.tags = tags_by_task.get(task.id, [])

        return tasks

    def _attach_attachments_to_tasks(self, tasks: List[Task]) -> List[Task]:
        if not tasks:
            return tasks

        task_ids = [t.id for t in tasks]
        placeholders = ",".join("?" * len(task_ids))

        cur = self._conn.cursor()
        cur.execute(
            f"""
            SELECT id, task_id, file_path, file_name
            FROM task_attachments
            WHERE task_id IN ({placeholders})
        """,
            task_ids,
        )

        attachments_by_task = {task_id: [] for task_id in task_ids}
        for row in cur.fetchall():
            att_id, task_id, file_path, file_name = row
            attachments_by_task[task_id].append(
                TaskAttachment(
                    id=att_id, task_id=task_id, file_path=file_path, file_name=file_name
                )
            )

        for task in tasks:
            task.attachments = attachments_by_task.get(task.id, [])

        return tasks

    def add_tag(self, tag: Tag) -> int:
        cur = self._conn.cursor()
        try:
            cur.execute(
                "INSERT INTO tags (name, color) VALUES (?, ?)", (tag.name, tag.color)
            )
            self._conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            return -1

    def get_all_tags(self) -> List[Tag]:
        cur = self._conn.cursor()
        cur.execute("SELECT id, name, color FROM tags")
        return [Tag(id=r[0], name=r[1], color=r[2]) for r in cur.fetchall()]

    def update_tag(self, tag: Tag) -> None:
        cur = self._conn.cursor()
        cur.execute(
            "UPDATE tags SET name=?, color=? WHERE id=?", (tag.name, tag.color, tag.id)
        )
        self._conn.commit()

    def delete_tag(self, tag_id: int) -> None:
        cur = self._conn.cursor()
        cur.execute("DELETE FROM task_tags WHERE tag_id=?", (tag_id,))
        cur.execute("DELETE FROM tags WHERE id=?", (tag_id,))
        self._conn.commit()

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
                task.color,  # NEW
            ),
        )
        task_id = cur.lastrowid

        if task.tags:
            for tag in task.tags:
                cur.execute(
                    "INSERT INTO task_tags (task_id, tag_id) VALUES (?, ?)",
                    (task_id, tag.id),
                )

        if task.attachments:
            for att in task.attachments:
                cur.execute(
                    "INSERT INTO task_attachments (task_id, file_path, file_name) VALUES (?, ?, ?)",
                    (task_id, att.file_path, att.file_name),
                )

        self._conn.commit()
        return task_id

    def get_all_tasks(self, search_query: str = "") -> List[Task]:
        """Fetches ACTIVE tasks, optionally filtered by a search keyword."""
        cur = self._conn.cursor()

        if search_query:
            # Add wildcards to match the string anywhere inside the field
            query = f"%{search_query}%"
            cur.execute(
                """
                SELECT * FROM tasks
                WHERE (is_deleted = 0 OR is_deleted IS NULL)
                AND (title LIKE ? OR description LIKE ?)
            """,
                (query, query),
            )
        else:
            cur.execute(
                "SELECT * FROM tasks WHERE is_deleted = 0 OR is_deleted IS NULL"
            )

        rows = cur.fetchall()
        tasks = [_row_to_task(r) for r in rows]
        tasks = self._attach_tags_to_tasks(tasks)
        return self._attach_attachments_to_tasks(tasks)

    def get_deleted_tasks(self, search_query: str = "") -> List[Task]:
        """Fetches TRASH tasks, optionally filtered by a search keyword."""
        cur = self._conn.cursor()

        if search_query:
            query = f"%{search_query}%"
            cur.execute(
                """
                SELECT * FROM tasks
                WHERE is_deleted = 1
                AND (title LIKE ? OR description LIKE ?)
            """,
                (query, query),
            )
        else:
            cur.execute("SELECT * FROM tasks WHERE is_deleted = 1")

        rows = cur.fetchall()
        tasks = [_row_to_task(r) for r in rows]
        tasks = self._attach_tags_to_tasks(tasks)
        return self._attach_attachments_to_tasks(tasks)

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
        row = cur.fetchone()
        if not row:
            return None
        task = _row_to_task(row)
        task = self._attach_tags_to_tasks([task])[0]
        return self._attach_attachments_to_tasks([task])[0]

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
        cur.execute("DELETE FROM task_tags WHERE task_id=?", (task.id,))
        if task.tags:
            for tag in task.tags:
                cur.execute(
                    "INSERT INTO task_tags (task_id, tag_id) VALUES (?, ?)",
                    (task.id, tag.id),
                )
        cur.execute("DELETE FROM task_attachments WHERE task_id=?", (task.id,))
        if task.attachments:
            for att in task.attachments:
                cur.execute(
                    "INSERT INTO task_attachments (task_id, file_path, file_name) VALUES (?, ?, ?)",
                    (task.id, att.file_path, att.file_name),
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
