# Prelim Laboratory Exam: Software Construction & Collaboration

## 1. Implemented Features Summary

The primary deliverable for Sprint 1 is a robust, responsive **Task Management System** developed using **PySide6** and ensures a scalable **Layered Architecture**.

**Core Features include:**
-   Full **CRUD capabilities** wherein users can Create, Read, Update, and Delete tasks.
-   Workflow management simplified with prioritized lists and instant "Mark as Done" functionality.
-   System integrity and user data security guaranteed through rigorous input validation and parameterized database queries.
-   Effective prevention of common vulnerabilities like SQL Injection while maintaining high performance with a local SQLite backend.

## 2. Coding Standards Applied

-   **Consistent Naming Conventions:** Applied to variables and functions for clear readability.
-   **Indentation and Formatting:** Maintained proper structure throughout the codebase.
-   **Comments:** Added where necessary to explain important logic.
-   **Modular Programming:** Principles were applied to separate concerns and improve maintainability.

## 3. Git Contribution Summary

-   **Version Control:** Git was used to manage version control throughout development.
-   **Commits:** Made regularly with meaningful messages describing the changes.
-   **Branching:** Utilized when implementing new features or fixes to keep the main branch stable.
-   **Repository:** Reflects continuous progress and organized updates.
  <img width="1201" height="809" alt="image" src="https://github.com/user-attachments/assets/0e91192d-467c-4b08-9789-3ad2c8946aa5" />
  <img width="1167" height="811" alt="image" src="https://github.com/user-attachments/assets/826c7d2a-8fcd-460c-bc84-1d0c60492159" />

  

## 4. Security Considerations

### SQL Injection Prevention #1

#### RISK IDENTIFICATION
**Where Risk Exists:** `src/business/task_manager.py` (Database Interaction Layer)

The application interacts with a local SQLite database to perform Create, Read, Update, and Delete (CRUD) operations. If user inputs (like "Task Title" or "Description") were directly concatenated into SQL strings using f-strings or `.format()`, a malicious user could input SQL commands (e.g., specific meta-characters) to manipulate the database structure or delete data (SQL Injection).

#### IMPLEMENTATION AND MITIGATION
**How We Addressed It:** We enforced the use of **Parameterized Queries** provided by the sqlite3 library. Instead of building query strings dynamically, we used placeholder syntax (`?`).

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

### Input Validation & Data Integrity #2

#### RISK IDENTIFICATION
**Where Risk Exists:** `src/presentation/add_task_dialog.py` (User Interface Layer)

Allowing invalid, empty, or extremely long inputs can lead to application instability, database errors (constraints violations), or confusing user experiences. While less severe than code injection in a desktop app, malformed data (like an empty title or whitespace-only strings) compromises the integrity of the data store and the reliability of the application's logic.

#### IMPLEMENTATION AND MITIGATION
**How We Addressed It:** We implemented Input Validation at the interface level before data is ever sent to the business logic or database.

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

**Sanitization:** `.strip()` removes accidental whitespace, preventing "blank" tasks that look empty but technically contain spaces.

**Validation:** Checking `if not title` ensures that every task has a valid identifier, preventing the creation of "ghost" tasks in the database.

## 5. Code Review & Reflection

The codebase is cleanly separated into **Presentation (UI)**, **Business Logic**, and **Data layers**. This internal structure makes the application highly maintainable and scalable, enabling you to modify the interface or database independently without breaking the core application logic.

**Areas for Improvement:**
-   **GitHub Collaboration:** Not all changes were discussed before being merged into the main branch. This can sometimes cause confusion or overlapping work. In the future, better communication and review before merging will improve teamwork.

**Lessons Learned:**
-   It is hard to complete tasks when group members are not on the same page.
-   Lack of clear communication can cause confusion and delays.
-   Regular updates and clear roles are important for better teamwork.
-   Good communication makes the implementation process smoother and more organized.

**Sprint 1 Code Review Outcomes:**
-   **Stability:** Confirmed that the EFFICIO application is stable and tailored to its core functional requirements.
-   **Technical Foundation:** Testing verified a smooth database initialization and application launch (Austria).
-   **Functionality:** Functional testing validated that all key task management features (Add, Edit, Delete, Mark as Done) operate correctly without major failures (Villafranca).
-   **Future Work:** While the current implementation is solid, user feedback indicates a need for a "Reminder Feature" to alert users of upcoming deadlines, which will be the primary focus for enhancement in Sprint 2.

### Group Members:
-   Austria, Arden Roland Nicholai M.
-   De La Paz, Jhoanna Alexandra C.
-   Emperador, Radge Michael A.
-   Mane, Jerstin M.
-   Villafranca, Richardson M.

