# QA RULE

## QA (name of task) - (QA Surname)
| Question  | Answer |
| :---: | :--- |
| What was tested? | (answer) |
| What passed/failed? | (answer) |

---

## QA Feature Implementation - Villafranca
| Question  | Answer |
| :---: | :--- |
| What was tested? | Functional Features, System Component, & Features Tested or Test Coverage |
| What passed/failed? | No Major Failures detected but needs a bit of tweaking such as adding a reminder feature on functional features|

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

---

## 2. Input Validation & Data Integrity

### **Risk Identification**
**Where Risk Exists:** `src/presentation/add_task_dialog.py` (User Interface Layer)

Allowing invalid, empty, or extremely long inputs can lead to application instability, database errors (constraints violations), or confusing user experiences. While less severe than code injection in a desktop app, malformed data (like an empty title or whitespace-only strings) compromises the integrity of the data store and the reliability of the application's logic.

### **Implementation & Mitigation**
**How We Addressed It:**
We implemented **Input Validation** at the interface level before data is ever sent to the business logic or database.

**Code Evidence (`src/presentation/add_task_dialog.py`):**
```python
def validate_and_accept(self):
    # Sanitize: Strip leading/trailing whitespace
    title = self.title_input.text().strip()
    
    # Validate: Ensure Title is not empty
    if not title:
        QMessageBox.warning(self, "Validation Error", "Title is required!")
        return  # Block submission
    
    self.accept()
```
*   **Sanitization:** `.strip()` removes accidental whitespace, preventing "blank" tasks that look empty but technically contain spaces.
*   **Validation:** Checking `if not title` ensures that every task has a valid identifier, preventing the creation of "ghost" tasks in the database.
