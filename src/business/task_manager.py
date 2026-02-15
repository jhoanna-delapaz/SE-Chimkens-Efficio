
from data.models import Task
from data.DataBaseHandler import create_connection

class TaskManager:
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = create_connection(self.db_file)

    def add_task(self, task: Task):
        sql = ''' INSERT INTO tasks(title, description, status, created_at, due_date, priority)
                  VALUES(?,?,?,?,?,?) '''
        cur = self.conn.cursor()
        cur.execute(sql, (task.title, task.description, task.status, task.created_at, task.due_date, task.priority))
        self.conn.commit()
        return cur.lastrowid

    def get_all_tasks(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM tasks")
        rows = cur.fetchall()
        tasks = []
        for row in rows:
            # simple mapping, assumes order
            tasks.append(Task(id=row[0], title=row[1], description=row[2], status=row[3], created_at=row[4], due_date=row[5], priority=row[6]))
        return tasks
