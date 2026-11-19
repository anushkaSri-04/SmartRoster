
from datetime import datetime, date

from app.extensions import db


# 1. POD MODEL

class Pod(db.Model):

    __tablename__ = "pods"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    lead_employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.id"),
        nullable=True
    )

    employees = db.relationship(
        "Employee",
        back_populates="pod",
        foreign_keys="Employee.pod_id"
    )

    lead_employee = db.relationship(
        "Employee",
        foreign_keys=[lead_employee_id]
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# 2. EMPLOYEE MODEL

class Employee(db.Model):

    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)

    employee_code = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    pod_id = db.Column(
        db.Integer,
        db.ForeignKey("pods.id"),
        nullable=True
    )

    # Monday = 0, Sunday = 6
    weekly_off = db.Column(
        db.Integer,
        nullable=False,
        default=6
    )

    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    pod = db.relationship(
        "Pod",
        back_populates="employees",
        foreign_keys=[pod_id]
    )

    assignments = db.relationship(
        "Assignment",
        back_populates="employee",
        cascade="all, delete-orphan"
    )

    leaves = db.relationship(
        "EmployeeLeave",
        back_populates="employee",
        cascade="all, delete-orphan"
    )


# 3. BRAND MODEL

class Brand(db.Model):

    __tablename__ = "brands"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    assignments = db.relationship(
        "Assignment",
        back_populates="brand",
        cascade="all, delete-orphan"
    )

    operating_rules = db.relationship(
        "OperatingRule",
        back_populates="brand",
        cascade="all, delete-orphan"
    )


# 4. PROCESS MODEL

class Process(db.Model):

    __tablename__ = "processes"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    assignments = db.relationship(
        "Assignment",
        back_populates="process"
    )

    operating_rules = db.relationship(
        "OperatingRule",
        back_populates="process"
    )


# 5. ASSIGNMENT MODEL

class Assignment(db.Model):

    __tablename__ = "assignments"

    id = db.Column(db.Integer, primary_key=True)

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.id"),
        nullable=False
    )

    brand_id = db.Column(
        db.Integer,
        db.ForeignKey("brands.id"),
        nullable=False
    )

    process_id = db.Column(
        db.Integer,
        db.ForeignKey("processes.id"),
        nullable=False
    )

    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    employee = db.relationship(
        "Employee",
        back_populates="assignments"
    )

    brand = db.relationship(
        "Brand",
        back_populates="assignments"
    )

    process = db.relationship(
        "Process",
        back_populates="assignments"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "employee_id",
            "brand_id",
            "process_id",
            name="unique_employee_brand_process"
        ),
    )



# 6. OPERATING RULE MODEL

class OperatingRule(db.Model):

    __tablename__ = "operating_rules"

    id = db.Column(db.Integer, primary_key=True)

    brand_id = db.Column(
        db.Integer,
        db.ForeignKey("brands.id"),
        nullable=False
    )

    process_id = db.Column(
        db.Integer,
        db.ForeignKey("processes.id"),
        nullable=False
    )

    # Python weekdays: Monday=0, Sunday=6
    # Example: [0, 1, 2, 3, 4, 5, 6]
    working_days = db.Column(
        db.JSON,
        nullable=False
    )

    holidays_open = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    min_staff = db.Column(
        db.Integer,
        default=1,
        nullable=False
    )

    weekly_off_policy = db.Column(
        db.String(30),
        nullable=False,
        default="require_backup"
    )

    brand = db.relationship(
        "Brand",
        back_populates="operating_rules"
    )

    process = db.relationship(
        "Process",
        back_populates="operating_rules"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "brand_id",
            "process_id",
            name="unique_brand_process_rule"
        ),
        db.CheckConstraint(
            "min_staff >= 0",
            name="check_min_staff_nonnegative"
        ),
    )


# 7. EMPLOYEE LEAVE MODEL

class EmployeeLeave(db.Model):

    __tablename__ = "employee_leaves"

    id = db.Column(db.Integer, primary_key=True)

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.id"),
        nullable=False
    )

    start_date = db.Column(
        db.Date,
        nullable=False
    )

    end_date = db.Column(
        db.Date,
        nullable=False
    )

    # planned_leave, comp_off, sick_leave
    leave_type = db.Column(
        db.String(30),
        nullable=False
    )

    # pending, approved, rejected
    status = db.Column(
        db.String(20),
        default="pending",
        nullable=False
    )

    employee = db.relationship(
        "Employee",
        back_populates="leaves"
    )

    __table_args__ = (
        db.CheckConstraint(
            "end_date >= start_date",
            name="check_leave_date_range"
        ),
    )


# 8. PUBLIC HOLIDAY MODEL

class PublicHoliday(db.Model):

    __tablename__ = "public_holidays"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(120),
        nullable=False
    )

    holiday_date = db.Column(
        db.Date,
        nullable=False
    )

    region = db.Column(
        db.String(100),
        nullable=True
    )

    __table_args__ = (
        db.UniqueConstraint(
            "holiday_date",
            "region",
            name="unique_holiday_region"
        ),
    )


# 9. ROSTER MODEL

class Roster(db.Model):

    __tablename__ = "rosters"

    id = db.Column(db.Integer, primary_key=True)

    month = db.Column(
        db.Integer,
        nullable=False
    )

    year = db.Column(
        db.Integer,
        nullable=False
    )

    # draft, validated, published
    status = db.Column(
        db.String(20),
        default="draft",
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    entries = db.relationship(
        "RosterEntry",
        back_populates="roster",
        cascade="all, delete-orphan"
    )

    conflicts = db.relationship(
        "Conflict",
        back_populates="roster",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "month",
            "year",
            name="unique_monthly_roster"
        ),
        db.CheckConstraint(
            "month BETWEEN 1 AND 12",
            name="check_roster_month"
        ),
    )


# 10. ROSTER ENTRY MODEL

class RosterEntry(db.Model):

    __tablename__ = "roster_entries"

    id = db.Column(db.Integer, primary_key=True)

    roster_id = db.Column(
        db.Integer,
        db.ForeignKey("rosters.id"),
        nullable=False
    )

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.id"),
        nullable=False
    )

    work_date = db.Column(
        db.Date,
        nullable=False
    )

    # working, weekly_off, leave, holiday, comp_off
    status = db.Column(
        db.String(30),
        nullable=False
    )

    roster = db.relationship(
        "Roster",
        back_populates="entries"
    )

    employee = db.relationship("Employee")
    tasks = db.relationship(
    "RosterEntryTask",
    back_populates="roster_entry",
    cascade="all, delete-orphan"
)

    __table_args__ = (
        db.UniqueConstraint(
            "roster_id",
            "employee_id",
            "work_date",
            name="unique_employee_roster_date"
        ),
    )


# 11. ROSTER ENTRY TASK MODEL

class RosterEntryTask(db.Model):

    __tablename__ = "roster_entry_tasks"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    roster_entry_id = db.Column(
        db.Integer,
        db.ForeignKey("roster_entries.id"),
        nullable=False
    )

    brand_id = db.Column(
        db.Integer,
        db.ForeignKey("brands.id"),
        nullable=False
    )

    process_id = db.Column(
        db.Integer,
        db.ForeignKey("processes.id"),
        nullable=False
    )

    roster_entry = db.relationship(
        "RosterEntry",
        back_populates="tasks"
    )

    brand = db.relationship("Brand")

    process = db.relationship("Process")

    __table_args__ = (
        db.UniqueConstraint(
            "roster_entry_id",
            "brand_id",
            "process_id",
            name="unique_roster_entry_task"
        ),
    )



# 11. CONFLICT MODEL

class Conflict(db.Model):

    __tablename__ = "conflicts"

    id = db.Column(db.Integer, primary_key=True)

    roster_id = db.Column(
        db.Integer,
        db.ForeignKey("rosters.id"),
        nullable=False
    )

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.id"),
        nullable=True
    )

    brand_id = db.Column(
        db.Integer,
        db.ForeignKey("brands.id"),
        nullable=True
    )

    process_id = db.Column(
        db.Integer,
        db.ForeignKey("processes.id"),
        nullable=True
    )

    conflict_date = db.Column(
        db.Date,
        nullable=True
    )

    severity = db.Column(
        db.String(20),
        nullable=False
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    is_resolved = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    roster = db.relationship(
        "Roster",
        back_populates="conflicts"
    )
