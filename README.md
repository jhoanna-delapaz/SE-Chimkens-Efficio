# SE-Chimkens-Efficio

**PROJECT DESCRIPTION**

EFFICIO is a task and performance tracker system designed to help individuals organize daily activities, meet deadlines, and improve productivity. By combining task management with performance analytics, EFFICIO provides users with clear insights into their progress, time usage, and overall efficiency—going beyond traditional to-do lists and basic note applications.

## Technical Architecture

### 1. Architectural Style
**Layered Architecture (Presentation, Business Logic, Data Access)**
The system follows a strict separation of concerns, ensuring that the User Interface is decoupled from the underlying logic and data storage.

### 2. High-Level Architecture Diagram
This diagram shows the major components and how data flows between them.

```mermaid
graph TD
    %% Styling
    classDef component fill:#fff,stroke:#666,stroke-width:1px;
    classDef user fill:#e1f5fe,stroke:#01579b,stroke-width:2px;

    User((User)):::user

    subgraph Presentation ["Presentation Layer (GUI)"]
        UI["MainWindow"]:::component
        Dash["Dashboard View"]:::component
    end

    subgraph Logic ["Business Logic Layer"]
        TM["Task Manager"]:::component
        Analytics["Analytics Engine"]:::component
    end

    subgraph Data ["Data Persistence Layer"]
        Repo["Data Handler"]:::component
        DB[("SQLite Database")]:::component
    end

    %% Key Interactions
    User -->|Interacts| UI
    
    UI <-->|Commands| TM
    Dash <-->|Reports| Analytics
    
    TM <-->|Tasks| Repo
    Analytics <-->|Stats| Repo
    
    Repo <-->|SQL| DB
```


### 3. Design Principles Applied

*   **Separation of Concerns (SoC):**
    The application is divided into distinct layers. The **UI** only handles user interaction and display. The **Business Logic (TaskManager)** handles rules and validation. The **Data Layer** handles storage. This makes the code easier to maintain and test.

*   **Single Responsibility Principle (SRP):**
    Each class has a focused purpose. For example, the `Analytics` class is solely responsible for calculating statistics and does not manage task creation or database connections.

## System Design (UML)

### 1. Use Case Diagram
**Scope:** Single-user, local application.
<br>
<img src="docs/uml/UML-%20UseCase%20(CHIMKENS)%20-%20EFFICIO.jpeg" width="600" alt="Use Case Diagram">
<br>

### 2. Class Diagram
**Tech Stack:** Python (Backend) + PyQt (Frontend).
<br>
<img src="docs/uml/UML-%20Class%20Diagram%20(CHIMKENS)%20-%20EFFICIO.jpeg" width="600" alt="Class Diagram">
<br>

### 3. Sequence Diagram (Add Task)
**Flow:** UI -> Controller -> Database.
<br>
<img src="docs/uml/UML-%20Sequence%20Diagram%20(CHIMKENS)%20-%20EFFICIO.jpeg" width="600" alt="Sequence Diagram">
<br>