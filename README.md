\# Smart Roster Management System



A web-based employee roster management system built with Flask and PostgreSQL. It helps operations teams manage employees, pods, brands, processes, availability, monthly work schedules and staffing conflicts from a centralized dashboard.



\*\*Live Application:\*\* https://smartroster-7sgl.onrender.com/  

\*\*GitHub Repository:\*\* https://github.com/anushkaSri-04/SmartRoster



\---



\## 1. Problem Statement



Organizations managing multiple brands and operational processes need to distribute employees across different responsibilities while maintaining adequate staffing coverage.



Manual roster preparation becomes difficult when teams have:



\- Multiple brands and processes.

\- Single-resource and multi-resource brands.

\- Different operating calendars.

\- Employee weekly offs and planned leaves.

\- Public holidays and compensatory offs.

\- Minimum staffing requirements.

\- Employees assigned to multiple brands or processes.



Smart Roster Management System addresses these challenges by providing a centralized platform for employee management, monthly roster generation, availability tracking and staffing conflict detection.



\## 2. Key Features



\### Employee Management

\- Create, view and update employee records.

\- Maintain employee codes, names, email addresses and pod assignments.

\- Configure weekly offs and employee active status.



\### Organizational Management

\- Manage multiple operational pods.

\- Maintain pod leads.

\- Create and manage brands.

\- Configure processes associated with brands.



\### Employee Assignments

\- Assign employees to brands and processes.

\- Support employees working across multiple brands.

\- Support brands with single-resource and multi-resource processes.



\### Operating Rules

\- Configure process-specific operating days.

\- Support different weekly operating calendars.

\- Configure holiday operating behavior.

\- Define minimum staffing requirements.

\- Configure weekly-off policies:

&#x20; - `require\_backup`: Keep the process open and report insufficient coverage when staffing requirements are not met.

&#x20; - `close\_process`: Allow the process to close when all assigned active employees are on weekly off.



\### Leave and Availability Management

\- Record planned leaves, sick leaves and compensatory offs.

\- Track approved leave requests.

\- Maintain public holiday records.

\- View employee availability and process coverage.



\### Monthly Roster Generation

\- Generate monthly rosters for the employee team.

\- Account for weekly offs, approved leaves, compensatory offs and holidays.

\- Allocate employees according to brand and process assignments.

\- Consider process operating rules and minimum staffing.

\- Balance allocations using workload-based selection.



\### Conflict Detection and Revalidation

\- Detect insufficient staffing coverage.

\- Identify process-level coverage gaps.

\- Revalidate coverage when roster assignments are manually changed.

\- Maintain conflict records associated with the affected date, brand and process.



\### Manual Roster Editing

\- Allow manual changes to draft rosters.

\- Validate employee availability and assignments before accepting changes.

\- Prevent duplicate brand-process assignments for the same roster entry.

\- Prevent edits to published rosters.

\- Recalculate affected process coverage after changes.



\### Multiple Views

The application provides centralized access to:

\- Company dashboard

\- Employee management

\- Pod management

\- Brand management

\- Process management

\- Assignment management

\- Operating rules

\- Leave management

\- Public holidays

\- Availability dashboard

\- Monthly rosters



\---



\## 3. Technology Stack



| Layer | Technology |

|---|---|

| Backend | Python, Flask |

| Frontend | HTML, CSS, Bootstrap, Jinja2 |

| Database | PostgreSQL |

| ORM | Flask-SQLAlchemy, SQLAlchemy |

| Database migrations | Flask-Migrate, Alembic |

| Configuration | python-dotenv |

| Testing | pytest |

| Application server | Gunicorn |

| Deployment | Render |

| Version control | Git and GitHub |



\---



\## 4. System Architecture



The application follows a modular Flask architecture.



```text

SmartRoster/

│

├── app/

│   ├── \_\_init\_\_.py

│   ├── config.py

│   ├── extensions.py

│   ├── models.py

│   ├── routes.py

│   │

│   ├── services/

│   │   ├── \_\_init\_\_.py

│   │   ├── availability.py

│   │   └── roster\_generator.py

│   │

│   ├── templates/

│   │   ├── base.html

│   │   ├── index.html

│   │   ├── employees/

│   │   ├── pods/

│   │   ├── brands/

│   │   ├── processes/

│   │   ├── assignments/

│   │   ├── leaves/

│   │   ├── operating\_rules/

│   │   ├── public\_holidays/

│   │   ├── availability/

│   │   └── rosters/

│   │

│   └── static/

│       └── css/

│           └── style.css

│

├── migrations/

├── tests/

│   └── test\_app.py

│

├── seed.py

├── run.py

├── wsgi.py

├── requirements.txt

├── Procfile

├── .env.example

├── .gitignore

└── README.md

```



\### Architecture Responsibilities



\- \*\*Models:\*\* Define database entities and relationships.

\- \*\*Routes:\*\* Handle HTTP requests, forms and application workflows.

\- \*\*Services:\*\* Implement roster-generation and availability business logic.

\- \*\*Templates:\*\* Render the application interface using Jinja2.

\- \*\*Migrations:\*\* Maintain database schema changes.

\- \*\*Seed script:\*\* Initialize demonstration data.

\- \*\*Tests:\*\* Verify application routes, roster changes and conflict handling.



\---



\## 5. Database Design



The system uses PostgreSQL with SQLAlchemy ORM.



The primary database entities are:



| Model | Responsibility |

|---|---|

| Pod | Stores operational teams |

| Employee | Stores employee information |

| Brand | Stores business brands |

| Process | Stores operational processes |

| Assignment | Maps employees to brands and processes |

| OperatingRule | Stores process-specific staffing and calendar rules |

| EmployeeLeave | Stores employee leave and comp-off records |

| PublicHoliday | Stores public holiday information |

| Roster | Represents a monthly roster |

| RosterEntry | Represents an employee's daily roster status |

| RosterEntryTask | Maps daily roster entries to brand-process responsibilities |

| Conflict | Records roster staffing and coverage conflicts |



\### Important Relationships



\- A pod can contain multiple employees.

\- Employees can have multiple brand-process assignments.

\- Brands can contain multiple processes.

\- Operating rules define how individual processes operate.

\- A monthly roster contains daily entries for employees.

\- A roster entry can contain multiple brand-process tasks.

\- Conflicts are associated with the affected brand, process and roster date.



The separate `RosterEntryTask` model supports employees handling multiple brand-process responsibilities on the same day.



\---



\## 6. Roster Generation Workflow



The roster generator follows a rule-based allocation approach.



\### Step 1: Validate the requested month



The system validates the requested month and year before generating the roster.



\### Step 2: Load operational data



The generator retrieves:



\- Active employees

\- Brand-process assignments

\- Operating rules

\- Approved employee leaves

\- Public holidays



\### Step 3: Create daily employee entries



For each active employee and each calendar day in the requested month, the system creates a roster entry.



Possible statuses include:



\- Working

\- Weekly Off

\- Leave

\- Holiday

\- Comp Off



\### Step 4: Apply employee availability



Before allocating tasks, the generator checks whether the employee is available on the requested date.



Employees unavailable because of weekly offs, approved leaves, holidays or compensatory offs are excluded from working allocations.



\### Step 5: Apply process operating rules



The generator checks whether the process should operate on the requested date.



It also applies the configured weekly-off policy and holiday behavior.



\### Step 6: Allocate employees



Available employees are selected using workload-based sorting.



The allocation considers:



1\. Current daily brand workload.

2\. Current monthly task workload.

3\. Employee ID as a deterministic tie-breaker.



This helps distribute work across employees rather than repeatedly assigning the same person.



\### Step 7: Validate minimum staffing



The system compares the number of allocated employees with the process's minimum staffing requirement.



When the requirement is not satisfied, the system records a coverage conflict.



\### Step 8: Save the roster



The generated roster, daily entries, task allocations and conflict records are saved in the database.



The generated roster initially has a draft status.



\---



\## 7. Conflict Handling



Conflict detection is an important part of the system.



Examples include:



\- A process requiring more employees than are available.

\- Employees being unavailable because of weekly offs or leave.

\- Insufficient staffing after a manual roster change.

\- Invalid employee-process assignments.

\- Duplicate brand-process responsibilities.



\### Weekly-Off Policy



\*\*require\_backup\*\*



The process remains operational, but the system reports a coverage gap if the minimum staffing requirement cannot be satisfied.



\*\*close\_process\*\*



The process can be marked closed when all assigned active employees are on weekly off.



\### Manual Change Revalidation



When a user changes a roster task, the application validates:



\- Whether the roster is still a draft.

\- Whether the selected employee is active.

\- Whether the employee is assigned to the relevant brand and process.

\- Whether the employee is working on that date.

\- Whether the process operates on that date.

\- Whether the change creates a duplicate task.



After a valid change, process coverage is recalculated and the corresponding conflict is created, updated or resolved.



\---



\## 8. Installation and Local Setup



\### Prerequisites



\- Python 3.11 or compatible Python version

\- PostgreSQL

\- Git

\- Visual Studio Code or another code editor



\### Step 1: Clone the repository



```bash

git clone https://github.com/anushkaSri-04/SmartRoster.git

cd SmartRoster

```



\### Step 2: Create a virtual environment



```bash

python -m venv venv

```



Activate it on Windows CMD:



```cmd

venv\\Scripts\\activate

```



\### Step 3: Install dependencies



```bash

pip install -r requirements.txt

```



\### Step 4: Configure environment variables



Create a `.env` file in the project root using `.env.example` as a reference.



Example:



```env

SECRET\_KEY=replace-with-a-secure-random-secret

DATABASE\_URL=postgresql+psycopg://username:password@localhost:5432/smartroster

```



Use your own PostgreSQL database credentials.



Never commit `.env` or publish database credentials.



\### Step 5: Apply database migrations



```bash

python -m flask --app run.py db upgrade

```



\### Step 6: Seed initial data



```bash

python seed.py

```



\### Step 7: Start the application



```bash

python run.py

```



Open:



```text

http://127.0.0.1:5000/

```



\---



\## 9. Testing



The project uses pytest.



Run the test suite:



```bash

pytest -v

```



The implemented test coverage includes:



\- Homepage and health endpoint responses.

\- Successful roster-task reassignment.

\- Rejection of unassigned employees.

\- Rejection of employees on weekly off or leave.

\- Prevention of duplicate task assignments.

\- Prevention of editing published rosters.

\- Process coverage conflict revalidation.



The development test suite previously completed successfully with \*\*12 passing tests\*\*.



\---



\## 10. Deployment



The application is deployed using Render.



\### Deployment Configuration



| Setting | Value |

|---|---|

| Repository | anushkaSri-04/SmartRoster |

| Branch | main |

| Build command | `pip install -r requirements.txt` |

| Start command | `gunicorn wsgi:app` |

| Database | Render PostgreSQL |



\### Environment Variables



Configure the following in Render:



\- `SECRET\_KEY`

\- `DATABASE\_URL`



Use the PostgreSQL connection string appropriate for the deployed service.



\### Database Initialization



After deployment, apply migrations:



```bash

python -m flask --app run.py db upgrade

```



Then initialize demonstration data:



```bash

python seed.py

```



For this deployment, these commands were executed locally using the Render PostgreSQL external connection because the Render Shell was unavailable on the selected service plan.



\---



\## 11. Demonstration Dataset



The deployed database was initialized with the following demonstration records:



| Entity | Count |

|---|---:|

| Employees | 30 |

| Pods | 5 |

| Brands | 30 |

| Processes | 5 |

| Assignments | 61 |

| Operating Rules | 58 |

| Public Holidays | 3 |



The dataset includes single-resource and multi-resource brand configurations.



\---



\## 12. Eight Key Design Decisions



\### 1. Why use Flask?



Flask provides a lightweight and modular backend framework. It allows the application to separate routes, database models and business logic into independent modules.



\### 2. Why use PostgreSQL?



PostgreSQL provides relational data management and transaction support, making it suitable for employee assignments, roster records and relationships between operational entities.



\### 3. Why separate brands and processes?



A brand may operate multiple processes, and each process may have different staffing requirements and working calendars. Separating them allows independent configuration.



\### 4. Why use a separate Assignment model?



Employees may work across multiple brands and processes. A separate assignment entity supports this many-to-many relationship without duplicating employee or brand records.



\### 5. Why configure operating rules per process?



Different processes may follow different operating calendars, holiday policies and minimum staffing requirements. Process-level rules provide the flexibility needed to represent these differences.



\### 6. How is employee workload balanced?



The allocation algorithm sorts available employees by daily brand workload, monthly task workload and employee ID. This provides a deterministic, workload-aware allocation approach.



\### 7. How are conflicts handled?



The system compares allocated staffing with minimum staffing requirements and records coverage gaps. Manual changes trigger revalidation so that conflicts can be updated or resolved.



\### 8. How are future changes supported?



The modular architecture, separate business models, configurable operating rules and service layer make it easier to extend the system with additional allocation strategies, scheduling constraints, analytics and operational workflows.



\---



\## 13. Current Scope and Future Enhancements



\### Implemented



\- Employee and pod management.

\- Brand and process management.

\- Employee assignments.

\- Configurable operating rules.

\- Leave and holiday management.

\- Employee availability.

\- Monthly roster generation.

\- Workload-based task allocation.

\- Coverage conflict detection.

\- Manual roster editing and revalidation.

\- PostgreSQL integration.

\- Render deployment.



\### Potential Future Enhancements



\- Authentication and role-based access control.

\- More advanced workload optimization.

\- Shift-based scheduling when shift requirements are defined.

\- Automated notifications for staffing conflicts.

\- Export rosters to Excel or PDF.

\- Historical roster analytics.

\- Automated backup and audit logging.



\---



\## 14. Project Status



Smart Roster Management System has been implemented using Flask, PostgreSQL and a rule-based roster allocation approach.



The application is deployed and accessible online.



\*\*Live Demo:\*\* https://smartroster-7sgl.onrender.com/



\*\*Source Code:\*\* https://github.com/anushkaSri-04/SmartRoster



\---



\## License



This project was developed as an internship assessment project. Add an appropriate license if redistribution is intended.



