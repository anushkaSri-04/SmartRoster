
import calendar
from collections import defaultdict
from datetime import date

from app.extensions import db
from app.models import (
    Employee,
    Assignment,
    OperatingRule,
    EmployeeLeave,
    PublicHoliday,
    Roster,
    RosterEntry,
    RosterEntryTask,
    Conflict,
    Brand
)


def generate_monthly_roster(month, year, region=None):
    """
    Generate a draft monthly roster.

    Supports two weekly-off policies:

    1. require_backup:
       Keep the process open and report a coverage gap
       if minimum staffing is not available.

    2. close_process:
       Close the process when all employees assigned to
       that brand-process combination are on weekly off.

    Returns:
        A dictionary containing roster details,
        allocation count, and coverage conflicts.
    """

    # -----------------------------------------
    # 1. VALIDATE INPUT
    # -----------------------------------------

    if not 1 <= month <= 12:
        raise ValueError("Month must be between 1 and 12.")

    if year < 2000:
        raise ValueError("Please provide a valid year.")

    employees = Employee.query.filter_by(
        is_active=True
    ).order_by(Employee.id).all()

    if not employees:
        raise ValueError("No active employees found.")

    first_day = date(year, month, 1)

    last_day = date(
        year,
        month,
        calendar.monthrange(year, month)[1]
    )

    # -----------------------------------------
    # 2. GET OR CREATE MONTHLY ROSTER
    # -----------------------------------------

    roster = Roster.query.filter_by(
        month=month,
        year=year
    ).first()

    if roster and roster.status == "published":
        raise ValueError(
            "A published roster cannot be regenerated."
        )

    if not roster:

        roster = Roster(
            month=month,
            year=year,
            status="draft"
        )

        db.session.add(roster)
        db.session.flush()

    else:

        roster.entries.clear()
        roster.conflicts.clear()
        roster.status = "draft"

        db.session.flush()

    # -----------------------------------------
    # 3. FETCH RELEVANT DATA
    # -----------------------------------------

    rules = (
        OperatingRule.query
        .join(Brand, OperatingRule.brand_id == Brand.id)
        .filter(Brand.is_active.is_(True))
        .all()
    )

    assignments = Assignment.query.filter_by(
        is_active=True
    ).all()

    approved_leaves = EmployeeLeave.query.filter(
        EmployeeLeave.status == "approved",
        EmployeeLeave.start_date <= last_day,
        EmployeeLeave.end_date >= first_day
    ).all()

    holidays = PublicHoliday.query.filter(
        PublicHoliday.holiday_date >= first_day,
        PublicHoliday.holiday_date <= last_day
    ).all()

    # -----------------------------------------
    # 4. INDEX ASSIGNMENTS
    # -----------------------------------------

    assignment_map = defaultdict(list)

    for assignment in assignments:

        if (
            assignment.employee
            and assignment.employee.is_active
            and assignment.brand
            and assignment.brand.is_active
        ):

            key = (
                assignment.brand_id,
                assignment.process_id
            )

            assignment_map[key].append(
                assignment.employee
            )

    # -----------------------------------------
    # 5. INDEX APPROVED LEAVES
    # -----------------------------------------

    leave_map = defaultdict(dict)

    for leave in approved_leaves:

        current_date = max(
            leave.start_date,
            first_day
        )

        end_date = min(
            leave.end_date,
            last_day
        )

        while current_date <= end_date:

            leave_map[leave.employee_id][current_date] = (
                leave.leave_type
            )

            current_date = date.fromordinal(
                current_date.toordinal() + 1
            )

    # -----------------------------------------
    # 6. INDEX PUBLIC HOLIDAYS
    # -----------------------------------------

    holiday_map = defaultdict(list)

    for holiday in holidays:

        holiday_map[holiday.holiday_date].append(
            holiday
        )

    # -----------------------------------------
    # 7. CREATE DAILY EMPLOYEE ROSTER ENTRIES
    # -----------------------------------------

    entry_map = {}

    current_date = first_day

    while current_date <= last_day:

        applicable_holidays = [
            holiday
            for holiday in holiday_map[current_date]
            if holiday.region is None
            or (
                region is not None
                and holiday.region.lower() == region.lower()
            )
        ]

        is_holiday = bool(applicable_holidays)

        for employee in employees:

            leave_type = leave_map[employee.id].get(
                current_date
            )

            if employee.weekly_off == current_date.weekday():

                status = "weekly_off"

            elif leave_type == "comp_off":

                status = "comp_off"

            elif leave_type:

                status = "leave"

            elif is_holiday:

                status = "holiday"

            else:

                status = "working"

            entry = RosterEntry(
                roster=roster,
                employee=employee,
                work_date=current_date,
                status=status
            )

            db.session.add(entry)

            entry_map[
                (employee.id, current_date)
            ] = entry

        current_date = date.fromordinal(
            current_date.toordinal() + 1
        )

    db.session.flush()

    # -----------------------------------------
    # 8. TRACK EMPLOYEE WORKLOAD
    # -----------------------------------------

    daily_brand_load = defaultdict(set)

    monthly_task_load = defaultdict(int)

    coverage_gaps = 0

    allocated_tasks = 0

    # -----------------------------------------
    # 9. GENERATE DAILY PROCESS ALLOCATIONS
    # -----------------------------------------

    current_date = first_day

    while current_date <= last_day:

        weekday = current_date.weekday()

        applicable_holidays = [
            holiday
            for holiday in holiday_map[current_date]
            if holiday.region is None
            or (
                region is not None
                and holiday.region.lower() == region.lower()
            )
        ]

        is_holiday = bool(applicable_holidays)

        for rule in rules:

            key = (
                rule.brand_id,
                rule.process_id
            )

            # ---------------------------------
            # CHECK PROCESS OPERATING CALENDAR
            # ---------------------------------

            if weekday not in (rule.working_days or []):
                continue

            if is_holiday and not rule.holidays_open:
                continue

            minimum_required = rule.min_staff

            if minimum_required <= 0:
                continue

            # ---------------------------------
            # GET ASSIGNED EMPLOYEES
            # ---------------------------------

            candidates = assignment_map.get(
                key,
                []
            )

            # ---------------------------------
            # WEEKLY-OFF POLICY
            # ---------------------------------

            weekly_off_policy = getattr(
                rule,
                "weekly_off_policy",
                "require_backup"
            )

            all_assigned_employees_on_weekly_off = (
                bool(candidates)
                and all(
                    employee.weekly_off == weekday
                    for employee in candidates
                )
            )

            # Policy 1:
            # Close the process only when EVERY
            # assigned employee is on weekly off.
            #
            # Approved leaves do not trigger closure.

            if (
                weekly_off_policy == "close_process"
                and all_assigned_employees_on_weekly_off
            ):

                continue

            # ---------------------------------
            # FIND AVAILABLE EMPLOYEES
            # ---------------------------------

            available_candidates = []

            for employee in candidates:

                # Exclude employees on weekly off.
                if employee.weekly_off == weekday:
                    continue

                # Exclude employees on approved leave.
                if current_date in leave_map[employee.id]:
                    continue

                available_candidates.append(
                    employee
                )

            # ---------------------------------
            # WORKLOAD BALANCING
            # ---------------------------------

            available_candidates.sort(
                key=lambda employee: (
                    len(
                        daily_brand_load[
                            (employee.id, current_date)
                        ]
                    ),
                    monthly_task_load[employee.id],
                    employee.id
                )
            )

            # Select employees according to minimum staffing.
            selected = available_candidates[
                :minimum_required
            ]

            # ---------------------------------
            # CREATE EMPLOYEE TASKS
            # ---------------------------------

            for employee in selected:

                entry = entry_map[
                    (employee.id, current_date)
                ]

                task = RosterEntryTask(
                    roster_entry=entry,
                    brand_id=rule.brand_id,
                    process_id=rule.process_id
                )

                db.session.add(task)

                entry.status = "working"

                daily_brand_load[
                    (employee.id, current_date)
                ].add(rule.brand_id)

                monthly_task_load[employee.id] += 1

                allocated_tasks += 1

            # ---------------------------------
            # DETECT COVERAGE GAPS
            # ---------------------------------

            if len(selected) < minimum_required:

                gap = minimum_required - len(selected)

                coverage_gaps += 1

                conflict = Conflict(
                    roster=roster,
                    brand_id=rule.brand_id,
                    process_id=rule.process_id,
                    conflict_date=current_date,
                    severity="high",
                    message=(
                        f"{rule.brand.name} - "
                        f"{rule.process.name}: "
                        f"requires {minimum_required} employees, "
                        f"but only {len(selected)} are available. "
                        f"Shortage: {gap}. "
                        f"Weekly-off policy: {weekly_off_policy}."
                    ),
                    is_resolved=False
                )

                db.session.add(conflict)

        current_date = date.fromordinal(
            current_date.toordinal() + 1
        )

    # -----------------------------------------
    # 10. SAVE ROSTER
    # -----------------------------------------

    db.session.commit()

    return {
        "roster_id": roster.id,
        "month": month,
        "year": year,
        "employee_count": len(employees),
        "allocated_tasks": allocated_tasks,
        "coverage_gaps": coverage_gaps,
        "status": roster.status
    }
