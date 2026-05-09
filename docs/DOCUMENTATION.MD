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

## QA Feature Implementation - Villafranca
| Question  | Answer |
| :---: | :--- |
| What was tested? | Functional Features, System Component, & Features Tested or Test Coverage |
| What passed/failed? | No Major Failures detected but needs a bit of tweaking such as adding a reminder feature on functional features|

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
**Where Risk Exists:** `src/data/database_handler.py` (Database Interaction Layer)

The application interacts with a local SQLite database to perform Create, Read, Update, and Delete (CRUD) operations. If user inputs (like "Task Title" or "Description") were directly concatenated into SQL strings using f-strings or `.format()`, a malicious user could input SQL commands (e.g., specific meta-characters) to manipulate the database structure or delete data (SQL Injection).

### **Implementation & Mitigation**
**How We Addressed It:**
We enforced the use of **Parameterized Queries** provided by the `sqlite3` library. Instead of building query strings dynamically, we used placeholder syntax (`?`).

**Code Evidence (`src/data/database_handler.py`):**
```python
# SECURE: Using '?' placeholder
cur.execute(
    """INSERT INTO tasks
       (title, description, status, created_at, due_date, priority, is_deleted, color)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
    (task.title, task.description or "", task.status, ...)
)

# VULNERABLE (Avoided):
# sql = f"INSERT INTO tasks... VALUES('{task.title}', ...)"
```
By using `?`, the database driver treats the inputs strictly as data, not executable code, effectively neutralizing SQL injection attacks.

---

## 2. Input Validation & Data Integrity

### **Risk Identification**
**Where Risk Exists:** `src/presentation/task_editor_dialog.py` (User Interface Layer)

Allowing invalid, empty, or extremely long inputs can lead to application instability, database errors (constraints violations), or confusing user experiences. While less severe than code injection in a desktop app, malformed data (like an empty title or whitespace-only strings) compromises the integrity of the data store and the reliability of the application's logic.

### **Implementation & Mitigation**
**How We Addressed It:**
We implemented **Input Validation** at the interface level before data is ever sent to the business logic or database.

**Code Evidence (`src/presentation/task_editor_dialog.py`):**
```python
def validate_and_accept(self):
    title = self.title_input.text().strip()

    if not title:
        self.toast.show_toast("Title is required!")
        return

    # ISO 25010 Security & Data Integrity: Sync with TaskManager validation
    if len(title) > 255:
        self.toast.show_toast("Title is too long (max 255)!")
        return

    malicious_patterns = ["<script>", "javascript:", "onload="]
    if any(p in title.lower() for p in malicious_patterns):
        self.toast.show_toast("Invalid characters detected!")
        return

    self.accept()
```
*   **Sanitization:** `.strip()` removes accidental whitespace.
*   **Length Constraint:** Enforcing a 255-character limit prevents database overflow and UI breakage.
*   **Anti-XSS:** Blocking script-like patterns prevents potential malicious content from being stored.

---

## 3. Architectural Integrity & Layered Responsibility

### **Risk Identification**
**Where Risk Exists:** `src/business/task_manager.py` vs `src/data/database_handler.py`

Implementing business rules (like how long a task stays in the Trash before being deleted) directly in the database layer creates tight coupling and makes the system harder to maintain. If the rules change (e.g., from 14 days to 30 days), developers shouldn't have to modify low-level SQL handling code.

### **Implementation & Mitigation**
**How We Addressed It:**
We refactored the **3-Stage Lifecycle** (Auto-Cleanup) to ensure that the data layer only executes commands, while the business layer defines the rules.

**Code Evidence (`src/business/task_manager.py`):**
```python
def run_auto_cleanup(self) -> None:
    # Rule calculation happens HERE in the Business Layer
    archive_cutoff = now - timedelta(days=3)
    trash_cutoff = now - timedelta(days=14)

    # Execution is delegated to the Data Layer
    self._data_handler.run_auto_cleanup(archive_cutoff, trash_cutoff, ...)
```
By centralizing rules in `TaskManager`, we improve the **Maintainability** and **Analyzability** of the project, adhering to the ISO 25010 standard.
