

# Team Contribution & Agile Workflow Guidelines

This document serves as the official guide for our project's development. By following these standards, we ensure that our AI system meets the **ISO/IEC 25010** quality attributes of **Reliability**, **Maintainability**, and **Functional Suitability**.

---

## 1. Requirement Tagging & Hierarchy
To maintain high **Analyzability**, every task must be categorized using the team's hierarchical ID system. This allows us to trace every line of code back to its original Epic or User Story.

### **The ID System**
| Category | Prefix | Purpose | Example |
| :--- | :--- | :--- | :--- |
| **Epic** | `EP##` | Large project milestones. | `EP01: MLOps Infrastructure` |
| **Feature** | `FT##` | Specific functionality being added. | `FT01: Data Scraper` |
| **Task / Subtask** | `TK##` | The actual work unit. | `TK01: Install Pandas` |
| **Bug/Hotfix** | `HF##` | Repairs for errors in existing code. | `HF01: Fix Null Pointer` |
| **Documentation** | `DN##` | Any non-code, document-only changes. | `DN01: Research APA Citations` |

### **Linking Tasks (Traceability)**
Tasks must be linked to their parent Epic, User Story, or Bug.
* **Under an Epic:** `[EP01-TK01]` (Epic 01, Task 01)
* **Under a User Story:** `[US01-TK01]` (User Story 01, Task 01)
* **Under a Bug Fix:** `[HF01-TK01]` (Bug 01, Task 01)

---

## 2. The Agile Lifecycle: Starting a Task
We operate in **1-week Sprints**. No code should be written unless it is tied to an official ticket on our Project Board.

### **The "No Ticket, No Work" Rule**
1.  **Create an Issue:** Use the hierarchical ID in the title (e.g., `[US01-TK01] Create cleaning script`).
2.  **Assign & Move:** Move the card to **"In Progress"** on the GitHub Project Board.
3.  **Note the GitHub ID:** Every issue has an automated number (e.g., `#12`). You will use both IDs in your commits.

---

## 3. Branching Mechanics & Permissions
We follow a strict hierarchy to ensure that the "Production" version of our project never breaks. Each branch has a specific **Stability Level** and **Content Requirement**.

### **The Branch Hierarchy**

| Branch | Stability | What Goes Here? | Deployment Goal |
| :--- | :--- | :--- | :--- |
| **`main`** | **Stable** | Only "Production-Ready" code. This is the version the professor grades. No experimental code allowed. | **Final Release / Midterm Submission** |
| **`develop`** | **Integration** | All finished and peer-reviewed Features/Tasks. This is our "working prototype." | **Sprint Review / Integration Testing** |
| **`feature/`** | **Experimental** | Active coding, trial-and-error, and individual tasks. Anything goes here. | **Individual Task Completion** |

---

### **Detailed Branch Definitions**

#### **1. The `main` Branch (The Golden Version)**
* **Permissions:** **Locked.** No one commits directly to `main`.
* **What goes in:** Only merges from `develop` once a Sprint is 100% complete.
* **Condition:** Every line of code must be fully documented, and all MLOps monitoring must be functional.
* **ISO 25010 Goal:** **Reliability.** If the professor clones this branch, it *must* work perfectly.

#### **2. The `develop` Branch (The Melting Pot)**
* **Permissions:** **Protected.** No direct commits and Merges only via Pull Requests for code files. Automation and Documentation Files are applied here. 
* **What goes in:** Code that has passed all unit tests and has been "Approved" by a teammate. Documentation files are also allowed here.
* **Condition:** The code doesn't have to be "polished," but it must not break the project for other teammates.
* **ISO 25010 Goal:** **Functional Suitability.** Does this version have all the features we promised for the Sprint?

#### **3. The `feature/` Branches (The Workbench)**
* **Permissions:** **Open.** The owner of the task can commit as much as they want.
* **What goes in:** Draft code, new model experiments, messy scripts, and temporary files.
* **Condition:** Branches must be named using our **Hierarchical IDs** (e.g., `feature/US01-TK01-data-fix`).
* **ISO 25010 Goal:** **Maintainability.** By keeping "messy" work in these branches, we keep the rest of the project clean.

---

### **The "Promotion" Flow**
Code "moves up" the ladder as it gets more stable:
1.  **Work** happens in `feature/`.
2.  **Pull Request** moves code from `feature/` to `develop`. (**Squash and Merge**)
3.  **Final Review** moves code from `develop` to `main` at the end of the Sprint. (**Standard Merge**)

---
## 4. Branching Strategy (GitFlow Lite)
Always branch off of `develop`. **Never commit directly to `main` or `develop`.**

**Branch Naming Convention:** `feature/[PrimaryID]-[SubID]-description`
* **Example (Task under Epic):** `feature/EP01-TK01-setup-actions`
* **Example (Task under User Story):** `feature/US01-TK01-clean-data`

---

## 5. Development & Committing
We follow a specific commit pipeline to ensure the history is professional and auditable.

### **The Commit Pipeline Format**
`type: [Hierarchical-ID] description [GitHubID #]`

* **Features/User Stories:** `ftr: [FT01] short description [#12]` *(Used for commiting deliverables of assigned Feature/User Story tickets)*
* **Bugfixes:** `htfx: [HF01] short description [#15]` *(Used for commiting deliverables of assigned Bugfix tickets)*
* **Epic-Level Tasks:** `epc: [EP01-TK01] short description [#20]` *(Used for commiting deliverables of Tasks under Epics)*
* **Tasks/Subtasks:** `tsk: [TK01] short description [#25]` *(Used for commiting deliverables of assigned Task tickets)*
* **Documentation:** `dcmnt: [DN01] short description` *(For adding or updating documents only)*
* **Syncing branches** `upd: [TK01] short description` *(For pulling branches into another branch)*
* **Chores / Maintenance:** `chore: [No-ID] short description` *(Used for updating requirements.txt, fixing typos, or small config files. No GitHub Issue ticket required).*
* **Code Refactoring:** `refactor: [No-ID] short description` *(Used for making existing code cleaner without changing features. No GitHub Issue ticket required).*

---

## 6. The Pull Request (PR) & Quality Gate
The PR is our "Definition of Done." A task is not finished until the PR is merged.

### **Submission & Review Checklist**
1.  **Title:** `Type: [Hierarchical-ID] Task Name (#GitHubID)`
2.  **Automation:** Use `Closes #12` in the description to automate the Project Board.
3.  **CI/CD Verification:** Do not request a review until the GitHub Actions pipeline (Pytest & Flake8) shows a Green Checkmark.
4.  **Merge:** Once the verification is done and passed, select "Squash and Merge."

---

## 7. Merging Policy: Squash and Merge
We utilize two distinct merge strategies to maintain a clean yet traceable history, maximizing **ISO/IEC 25010** standards for **Analyzability** and **Recoverability**.

### **Policy A: Squash and Merge (Feature > Develop)**
**Goal:** To "clean up" the mess of daily coding and maintain a professional history.
* **Action:** Always select **"Squash and Merge"** on GitHub.
* **Why:** Feature branches often have messy "WIP" or "typo fix" commits. Squashing collapses that noise into one clean "Requirement Increment."
* **Title:** `type: [ID] Short Description [#GitHubID]`
* **Branch Cleanup:** Always delete the feature branch after a successful merge.

### **Policy B: Standard Merge (Develop > Main)**
**Goal:** To "record" the history of a major milestone or release.
* **Action:** Always select **"Create a Merge Commit"** (Standard Merge).
* **Why:** We must preserve the integration history of the `develop` branch. A standard merge creates a "handshake" in the Git graph that shows exactly when a stable version was finalized for grading.
* **Title:** `epc: [EP##] Milestone Title - Stable Release Version [#ID]`
* **Description:** This acts as a **Changelog** summarizing all features included in the release.

---

## 8. Quality Standards (ISO/IEC 25010)
* **Maintainability:** Through hierarchical tagging, we can instantly trace code to its origin Epic or User Story.
* **Reliability:** Automated CI checks and peer reviews prevent "untested" code from reaching `main`.
* **Functional Suitability:** Every task is physically linked to a requirement ID, ensuring we only build what is necessary for the project.

---

## 9. QA & Testing Standards
We follow a **Regression-First** testing policy to ensure **Reliability**.
* **Master Test Suite:** All test cases are defined in the Master Suite and mapped to Requirement IDs (e.g., `EP01-FT01`).
* **Execution Logs:** Every Sprint results in a new Execution Log. We do not duplicate test steps; we only record the **Result**, **Date**, and **Defect ID**.
* **Regression Testing:** Every cycle must re-verify core features from previous cycles to prevent "Silent Failures" common in ML systems. This is done using automated tests while new features are tested manually.

Should be documented like this for **regression cycles**:
| TC ID | Requirement | Cycle 1 Status | Cycle 2 Status | Notes (Cycle 2) |
| :--- | :--- | :--- | :--- | :--- |
| **TC-001** | EP01-FT01 | ✅ Pass (manual) | ❌ **Fail** (Automated UI Test) | **REGRESSION:** Task creation broke after adding Trash Bin logic. |
| **TC-007** | EP01-FT05 | N/A | ❌ **Fail** (New) | **NEW:** No pop-up confirmation on permanent delete. |

---

## Quick Commands for the Team
| Action | Command |
| :--- | :--- |
| **Start a task** | `git checkout develop` -> `git pull` -> `git checkout -b feature/US01-TK01-name` |
| **Save work** | `git add .` -> `git commit -m "tsk: [US01-TK01] added cleaning logic [#12]"` |
| **Push code** | `git push origin feature/US01-TK01-name` |
| **Sync with team** | `git checkout develop` -> `git pull` -> `git checkout feature/US01-TK01-name` -> `git merge develop` |



