# Smart Roster Management System

## Technical Approach and Design Decisions

### 1\. Objective

The objective of Smart Roster Management System is to automate monthly employee roster preparation for an organization operating multiple brands, processes and pods.

The system addresses the complexity of allocating employees across operational responsibilities while respecting availability, weekly offs, approved leaves, holidays, process operating calendars and minimum staffing requirements.

The solution focuses on rule-based scheduling, workload distribution, conflict detection and manual correction with automatic revalidation.

### 2\. Requirement Analysis

The system was designed around the following operational requirements:

* Support at least 30 employees.
* Organize employees into multiple pods.
* Support multiple brands and processes.
* Handle both single-resource and multi-resource brands.
* Allow employees to work across multiple brand-process combinations.
* Configure operating calendars and minimum staffing per process.
* Account for weekly offs, leaves, compensatory offs and public holidays.
* Generate monthly rosters for the complete employee team.
* Detect insufficient staffing and scheduling conflicts.
* Support manual roster changes followed by validation.

### 3\. Technology Selection

The application uses Flask for backend development, Jinja2 templates and Bootstrap for the user interface, and PostgreSQL for persistent relational data storage.

Flask was selected because its modular structure makes it possible to organize the application into routes, models and independent business services.

SQLAlchemy provides ORM-based database interaction, while Flask-Migrate and Alembic manage schema changes.

Pytest is used to validate important application workflows.

The application is deployed on Render using Gunicorn and PostgreSQL.

### 4\. Data Model Design

The database is organized around the operational entities of the organization.

The main entities are:

* Pod
* Employee
* Brand
* Process
* Assignment
* OperatingRule
* EmployeeLeave
* PublicHoliday
* Roster
* RosterEntry
* RosterEntryTask
* Conflict

A separate Assignment entity allows employees to be mapped to multiple brands and processes.

A separate RosterEntryTask entity allows one employee's daily roster entry to contain multiple brand-process responsibilities.

OperatingRule stores configurable process-level constraints rather than embedding operating policies directly into the roster-generation code.

This separation improves maintainability and makes it possible to change operational rules without redesigning the database.

### 5\. Roster Generation Approach

The system uses a rule-based, workload-aware allocation algorithm.

The workflow is:

1. Validate the requested month and year.
2. Retrieve active employees, assignments, operating rules, approved leaves and public holidays.
3. Create daily roster entries for each active employee.
4. Determine employee availability for each date.
5. Exclude employees who are unavailable because of weekly offs, approved leave, holidays or compensatory offs.
6. Check whether the relevant process operates on that date.
7. Select available employees based on current daily brand workload, monthly task workload and employee ID.
8. Allocate the required brand-process tasks.
9. Compare allocated staffing with minimum staffing requirements.
10. Record coverage conflicts where requirements are not met.
11. Save the roster and associated records.

The allocation method uses workload-based sorting rather than random employee selection. This makes the allocation more predictable and helps distribute work across available employees.

### 6\. Availability and Operating Rules

Employee availability and process availability are evaluated separately.

Employee availability considers:

* Weekly off.
* Approved planned leave.
* Approved sick leave.
* Compensatory off.
* Public holidays.

Process availability considers:

* Configured operating days.
* Holiday operating behavior.
* Minimum staffing requirements.
* Weekly-off staffing policy.

Two weekly-off policies are supported:

**require\_backup:** The process remains open, and insufficient coverage is reported when the staffing requirement cannot be met.

**close\_process:** The process may close when all assigned active employees are on weekly off.

This approach allows different operational processes to follow different rules.

### 7\. Conflict Detection and Manual Revalidation

The system does not assume that every generated roster will satisfy every staffing requirement.

When the number of allocated employees is below the configured minimum, a coverage conflict is recorded.

Manual roster editing is also supported.

Before accepting a change, the system validates that:

* The roster is in draft status.
* The selected employee is active.
* The employee has the required assignment.
* The employee is available on the selected date.
* The process operates on that date.
* The task does not create a duplicate brand-process assignment.

After a valid change, the affected process coverage is recalculated. The corresponding conflict can be created, updated or resolved based on the new staffing count.

This makes manual intervention part of the validation workflow rather than an uncontrolled change to the roster.

### 8\. Architecture and Maintainability

The project follows a modular Flask application structure.

* Models define persistent entities and relationships.
* Routes handle application requests and user interactions.
* Services implement availability and roster-generation logic.
* Templates render the user interface.
* Migrations manage database schema evolution.
* Tests validate important workflows.

Separating business logic from route handlers makes the application easier to maintain and extend.

### 9\. Testing and Deployment

The project uses pytest to validate application behavior.

The test suite covers homepage and health endpoints, successful task reassignment, employee eligibility checks, duplicate prevention, published-roster protection and conflict revalidation.

The application was deployed on Render with PostgreSQL as the production database.

Database migrations were applied using Flask-Migrate, and demonstration data was initialized using the seed script.

The deployed dataset contains 30 employees, 5 pods, 30 brands, 5 processes, 61 assignments, 58 operating rules and 3 public holidays.

### 10\. Design Trade-offs and Limitations

The current allocation method prioritizes availability and workload balancing using a deterministic sorting strategy.

It is not a mathematical optimization solver. It does not guarantee a globally optimal allocation across all employees, brands and processes.

The system detects staffing gaps rather than silently assigning unavailable employees to satisfy minimum staffing requirements.

Shift timings were not included because no shift-time requirements were specified.

Future improvements could include advanced optimization algorithms, role-based access control, notifications, roster exports and historical workload analytics.

### 11\. Conclusion

Smart Roster Management System provides a centralized solution for managing operational teams and generating monthly employee rosters.

Its main design strengths are configurable process-level rules, separate employee and process availability evaluation, workload-aware allocation, explicit conflict tracking and post-edit revalidation.

The application demonstrates how a modular Flask architecture and relational database can be used to address practical workforce scheduling requirements.

