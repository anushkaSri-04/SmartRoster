
import pytest
from datetime import date

from app import create_app
from app.extensions import db
from app.models import (
    Employee,
    Brand,
    Process,
    Assignment,
    OperatingRule,
    Roster,
    RosterEntry,
    RosterEntryTask,
    Conflict,
)
from app.routes import revalidate_process_coverage


@pytest.fixture
def app():

    test_app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })

    with test_app.app_context():
        db.create_all()

        yield test_app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def roster_data(app):

    with app.app_context():

        # CREATE EMPLOYEES
        employees = []

        for number in range(1, 6):

            employee = Employee(
                employee_code=f"TEST{number:03d}",
                name=f"Test Employee {number}",
                email=f"test{number}@example.com",
                weekly_off=4 if number == 4 else 6,
                is_active=True
            )

            db.session.add(employee)
            employees.append(employee)

        db.session.flush()

        # CREATE BRAND AND PROCESS
        brand = Brand(
            name="Test Brand",
            description="Brand for automated testing",
            is_active=True
        )

        process = Process(
            name="Test Process",
            description="Process for automated testing"
        )

        db.session.add_all([brand, process])
        db.session.flush()

        # CREATE ACTIVE ASSIGNMENTS
        # Employees 1, 2, 4 and 5 are assigned.
        # Employee 3 intentionally has no assignment.

        for employee in [
            employees[0],
            employees[1],
            employees[3],
            employees[4]
        ]:

            db.session.add(
                Assignment(
                    employee_id=employee.id,
                    brand_id=brand.id,
                    process_id=process.id,
                    is_active=True
                )
            )

        # CREATE OPERATING RULE
        rule = OperatingRule(
            brand_id=brand.id,
            process_id=process.id,
            working_days=[0, 1, 2, 3, 4, 5, 6],
            holidays_open=False,
            min_staff=1,
            weekly_off_policy="require_backup"
        )

        db.session.add(rule)

        # CREATE DRAFT ROSTER
        roster = Roster(
            month=11,
            year=2026,
            status="draft"
        )

        db.session.add(roster)
        db.session.flush()

        work_date = date(2026, 11, 20)

        # CREATE DAILY ROSTER ENTRIES
        entries = []

        statuses = [
            "working",
            "working",
            "working",
            "weekly_off",
            "leave"
        ]

        for employee, status in zip(employees, statuses):

            entry = RosterEntry(
                roster_id=roster.id,
                employee_id=employee.id,
                work_date=work_date,
                status=status
            )

            db.session.add(entry)
            entries.append(entry)

        db.session.flush()

        # CREATE INITIAL TASK
        task = RosterEntryTask(
            roster_entry_id=entries[0].id,
            brand_id=brand.id,
            process_id=process.id
        )

        db.session.add(task)
        db.session.commit()

        return {
            "roster_id": roster.id,
            "task_id": task.id,
            "brand_id": brand.id,
            "process_id": process.id,
            "employee_ids": [employee.id for employee in employees],
            "entry_ids": [entry.id for entry in entries],
            "work_date": work_date
        }


# ==========================================
# APPLICATION TESTS
# ==========================================

def test_homepage(client):

    response = client.get("/")

    assert response.status_code == 200
    assert b"Smart Roster Management System" in response.data


def test_health_endpoint(client):

    response = client.get("/health")

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "healthy"
    assert data["database"] == "connected"


# ==========================================
# MANUAL ROSTER EDITING TESTS
# ==========================================

def test_successful_task_reassignment(
    app,
    client,
    roster_data
):

    response = client.post(
        f"/roster-tasks/{roster_data['task_id']}/edit",
        data={
            "target_entry_id": roster_data["entry_ids"][1]
        },
        follow_redirects=False
    )

    assert response.status_code == 302

    with app.app_context():

        task = db.session.get(
            RosterEntryTask,
            roster_data["task_id"]
        )

        assert task.roster_entry_id == roster_data["entry_ids"][1]


def test_reject_employee_without_active_assignment(
    app,
    client,
    roster_data
):

    response = client.post(
        f"/roster-tasks/{roster_data['task_id']}/edit",
        data={
            "target_entry_id": roster_data["entry_ids"][2]
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b"not actively assigned" in response.data

    with app.app_context():

        task = db.session.get(
            RosterEntryTask,
            roster_data["task_id"]
        )

        assert task.roster_entry_id == roster_data["entry_ids"][0]


def test_reject_employee_on_weekly_off(
    app,
    client,
    roster_data
):

    response = client.post(
        f"/roster-tasks/{roster_data['task_id']}/edit",
        data={
            "target_entry_id": roster_data["entry_ids"][3]
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b"not available" in response.data

    with app.app_context():

        task = db.session.get(
            RosterEntryTask,
            roster_data["task_id"]
        )

        assert task.roster_entry_id == roster_data["entry_ids"][0]


def test_reject_employee_on_leave(
    app,
    client,
    roster_data
):

    response = client.post(
        f"/roster-tasks/{roster_data['task_id']}/edit",
        data={
            "target_entry_id": roster_data["entry_ids"][4]
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b"not available" in response.data

    with app.app_context():

        task = db.session.get(
            RosterEntryTask,
            roster_data["task_id"]
        )

        assert task.roster_entry_id == roster_data["entry_ids"][0]


def test_prevent_duplicate_task(
    app,
    client,
    roster_data
):

    with app.app_context():

        duplicate = RosterEntryTask(
            roster_entry_id=roster_data["entry_ids"][1],
            brand_id=roster_data["brand_id"],
            process_id=roster_data["process_id"]
        )

        db.session.add(duplicate)
        db.session.commit()

    response = client.post(
        f"/roster-tasks/{roster_data['task_id']}/edit",
        data={
            "target_entry_id": roster_data["entry_ids"][1]
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b"already has this process assigned" in response.data

    with app.app_context():

        original_task = db.session.get(
            RosterEntryTask,
            roster_data["task_id"]
        )

        assert original_task.roster_entry_id == roster_data["entry_ids"][0]


def test_prevent_editing_published_roster(
    app,
    client,
    roster_data
):

    with app.app_context():

        roster = db.session.get(
            Roster,
            roster_data["roster_id"]
        )

        roster.status = "published"
        db.session.commit()

    response = client.post(
        f"/roster-tasks/{roster_data['task_id']}/edit",
        data={
            "target_entry_id": roster_data["entry_ids"][1]
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b"Only draft rosters can be manually edited" in response.data

    with app.app_context():

        task = db.session.get(
            RosterEntryTask,
            roster_data["task_id"]
        )

        assert task.roster_entry_id == roster_data["entry_ids"][0]


# ==========================================
# CONFLICT REVALIDATION TESTS
# ==========================================

def test_reassignment_resolves_existing_conflict(
    app,
    client,
    roster_data
):

    with app.app_context():

        conflict = Conflict(
            roster_id=roster_data["roster_id"],
            brand_id=roster_data["brand_id"],
            process_id=roster_data["process_id"],
            conflict_date=roster_data["work_date"],
            severity="high",
            message="Test coverage gap",
            is_resolved=False
        )

        db.session.add(conflict)
        db.session.commit()

        conflict_id = conflict.id

    response = client.post(
        f"/roster-tasks/{roster_data['task_id']}/edit",
        data={
            "target_entry_id": roster_data["entry_ids"][1]
        },
        follow_redirects=False
    )

    assert response.status_code == 302

    with app.app_context():

        conflict = db.session.get(Conflict, conflict_id)

        assert conflict.is_resolved is True


def test_insufficient_staffing_creates_conflict(
    app,
    roster_data
):

    with app.app_context():

        rule = OperatingRule.query.filter_by(
            brand_id=roster_data["brand_id"],
            process_id=roster_data["process_id"]
        ).first()

        rule.min_staff = 2
        db.session.commit()

        result = revalidate_process_coverage(
            roster_id=roster_data["roster_id"],
            brand_id=roster_data["brand_id"],
            process_id=roster_data["process_id"],
            work_date=roster_data["work_date"]
        )

        db.session.commit()

        conflicts = Conflict.query.filter_by(
            roster_id=roster_data["roster_id"],
            brand_id=roster_data["brand_id"],
            process_id=roster_data["process_id"],
            conflict_date=roster_data["work_date"],
            is_resolved=False
        ).all()

        assert len(conflicts) == 1


def test_close_process_does_not_create_weekly_off_conflict(
    app,
    roster_data
):

    with app.app_context():

        rule = OperatingRule.query.filter_by(
            brand_id=roster_data["brand_id"],
            process_id=roster_data["process_id"]
        ).first()

        rule.weekly_off_policy = "close_process"

        # All actively assigned employees have Friday as weekly off.
        for employee_id in roster_data["employee_ids"]:
            employee = db.session.get(Employee, employee_id)

            if Assignment.query.filter_by(
                employee_id=employee_id,
                brand_id=roster_data["brand_id"],
                process_id=roster_data["process_id"],
                is_active=True
            ).first():

                employee.weekly_off = 4

        # Remove the existing task because the process is closed.
        RosterEntryTask.query.filter_by(
            brand_id=roster_data["brand_id"],
            process_id=roster_data["process_id"]
        ).delete()

        db.session.commit()

        revalidate_process_coverage(
            roster_id=roster_data["roster_id"],
            brand_id=roster_data["brand_id"],
            process_id=roster_data["process_id"],
            work_date=roster_data["work_date"]
        )

        db.session.commit()

        unresolved_conflicts = Conflict.query.filter_by(
            roster_id=roster_data["roster_id"],
            brand_id=roster_data["brand_id"],
            process_id=roster_data["process_id"],
            conflict_date=roster_data["work_date"],
            is_resolved=False
        ).count()

        assert unresolved_conflicts == 0


def test_revalidation_does_not_create_duplicate_conflicts(
    app,
    roster_data
):

    with app.app_context():

        rule = OperatingRule.query.filter_by(
            brand_id=roster_data["brand_id"],
            process_id=roster_data["process_id"]
        ).first()

        rule.min_staff = 2
        db.session.commit()

        # First validation
        revalidate_process_coverage(
            roster_id=roster_data["roster_id"],
            brand_id=roster_data["brand_id"],
            process_id=roster_data["process_id"],
            work_date=roster_data["work_date"]
        )

        db.session.commit()

        # Second validation of the same process and date
        revalidate_process_coverage(
            roster_id=roster_data["roster_id"],
            brand_id=roster_data["brand_id"],
            process_id=roster_data["process_id"],
            work_date=roster_data["work_date"]
        )

        db.session.commit()

        unresolved_conflicts = Conflict.query.filter_by(
            roster_id=roster_data["roster_id"],
            brand_id=roster_data["brand_id"],
            process_id=roster_data["process_id"],
            conflict_date=roster_data["work_date"],
            is_resolved=False
        ).all()

        assert len(unresolved_conflicts) == 1
