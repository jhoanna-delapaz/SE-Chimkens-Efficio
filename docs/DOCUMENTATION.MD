# QA RULE

## QA (name of task) - (QA Surname)
| Question  | Answer |
| :---: | :--- |
| What was tested? | (answer) |
| What passed/failed? | (answer) |

---

## QA DB initialization - Austria
| Question  | Answer |
| :---: | :--- |
| What was tested? | Database initialization, Main Window |
| What passed/failed? | It runs smoothly |

---

## Sprint Summary (Short Reflection)
<ul>
<li>Submit a short group summary (1–2 paragraphs):</li>
<ol>
<li>What features were completed in Sprint 1?</li>
<li>What challenges did the team encounter?</li>
<li>What will the team improve in the next sprint?</li>
</ol>
</ul>


## Answer:
In Sprint 1, our team completed the basic setup of the task manager application. We created the main system files and database, and started working on important features like adding a new task, viewing tasks on the dashboard, and adding a checkbox for tasks. These features helped us build the foundation of the system so we can continue improving it in the next sprint.

One challenge we experienced was making sure the backend and frontend parts worked together properly, especially when connecting the program to the database. We also had to adjust to working as a team and managing our tasks. In the next sprint, we plan to improve our teamwork, finish more features, and test the system more carefully to avoid errors.

---

# Secure Coding Awareness

This document identifies two critical security considerations relevant to the **EFFICIO Task Manager** and details how our implementation addresses them.

## 1. SQL Injection Prevention

### **Risk Identification**
**Where Risk Exists:** `src/business/task_manager.py` (Database Interaction Layer)

The application interacts with a local SQLite database to perform Create, Read, Update, and Delete (CRUD) operations. If user inputs (like "Task Title" or "Description") were directly concatenated into SQL strings using f-strings or `.format()`, a malicious user could input SQL commands (e.g., specific meta-characters) to manipulate the database structure or delete data (SQL Injection).

### **Implementation & Mitigation**
**How We Addressed It:**
We enforced the use of **Parameterized Queries** provided by the `sqlite3` library. Instead of building query strings dynamically, we used placeholder syntax (`?`).

**Code Evidence (`src/business/task_manager.py`):**
```python
# SECURE: Using '?' placeholder
sql = ''' INSERT INTO tasks(title, description, status, created_at, due_date, priority)
          VALUES(?,?,?,?,?,?) '''
cur.execute(sql, (task.title, task.description, ...))

# VULNERABLE (Avoided):
# sql = f"INSERT INTO tasks... VALUES('{task.title}', ...)"
```
By using `?`, the database driver treats the inputs strictly as data, not executable code, effectively neutralizing SQL injection attacks.
