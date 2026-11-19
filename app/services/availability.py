
from app.models import (
    Employee,
    EmployeeLeave,
    Assignment,
    OperatingRule,
    PublicHoliday,
    Brand
)


def check_date_availability(target_date, region=None):
    """
    Checks employee availability and staffing coverage
    for every active brand-process combination on a date.

    Supports:
        require_backup:
            Process remains open. Report a coverage gap
            if available employees are below minimum staffing.

        close_process:
            Process closes when all assigned employees
            are on their weekly off.

    Approved leaves never trigger automatic process closure.
    """

    # -----------------------------------------
    # 1. FIND APPLICABLE PUBLIC HOLIDAYS
    # -----------------------------------------

    holidays = PublicHoliday.query.filter_by(
        holiday_date=target_date
    ).all()

    applicable_holidays = [
        holiday for holiday in holidays
        if holiday.region is None
        or (
            region is not None
            and holiday.region.lower() == region.lower()
        )
    ]

    is_public_holiday = bool(applicable_holidays)

    # -----------------------------------------
    # 2. FIND APPROVED LEAVES
    # -----------------------------------------

    approved_leaves = EmployeeLeave.query.filter(
        EmployeeLeave.status == "approved",
        EmployeeLeave.start_date <= target_date,
        EmployeeLeave.end_date >= target_date
    ).all()

    employees_on_leave = {
        leave.employee_id: leave.leave_type
        for leave in approved_leaves
    }

    # -----------------------------------------
    # 3. FETCH ACTIVE OPERATING RULES
    # -----------------------------------------

    rules = (
        OperatingRule.query
        .join(Brand, OperatingRule.brand_id == Brand.id)
        .filter(Brand.is_active.is_(True))
        .all()
    )

    results = []

    weekday = target_date.weekday()

    # -----------------------------------------
    # 4. EVALUATE EACH BRAND-PROCESS RULE
    # -----------------------------------------

    for rule in rules:

        # Check configured working calendar.
        is_working_day = (
            weekday in (rule.working_days or [])
        )

        # Check public holiday operation.
        is_open = (
            is_working_day
            and (
                not is_public_holiday
                or rule.holidays_open
            )
        )

        # -------------------------------------
        # 5. GET ACTIVE ASSIGNMENTS
        # -------------------------------------

        assignments = Assignment.query.filter_by(
            brand_id=rule.brand_id,
            process_id=rule.process_id,
            is_active=True
        ).all()

        assigned_employees = [
            assignment.employee
            for assignment in assignments
            if assignment.employee
            and assignment.employee.is_active
        ]

        available_employees = []
        unavailable_employees = []

        # -------------------------------------
        # 6. CHECK WEEKLY-OFF POLICY
        # -------------------------------------

        weekly_off_policy = getattr(
            rule,
            "weekly_off_policy",
            "require_backup"
        )

        all_assigned_employees_on_weekly_off = (
            bool(assigned_employees)
            and all(
                employee.weekly_off == weekday
                for employee in assigned_employees
            )
        )

        closed_reason = None

        # Normal calendar closure.
        if not is_working_day:

            closed_reason = "Not a configured working day"

        elif is_public_holiday and not rule.holidays_open:

            closed_reason = "Public holiday"

        # Policy: close process when every assigned
        # employee is on their weekly off.
        elif (
            is_open
            and weekly_off_policy == "close_process"
            and all_assigned_employees_on_weekly_off
        ):

            is_open = False

            closed_reason = (
                "All assigned employees are on weekly off"
            )

        # -------------------------------------
        # 7. IDENTIFY AVAILABLE EMPLOYEES
        # -------------------------------------

        if is_open:

            for employee in assigned_employees:

                reason = None

                if employee.weekly_off == weekday:

                    reason = "Weekly Off"

                elif employee.id in employees_on_leave:

                    leave_type = employees_on_leave[employee.id]

                    reason = (
                        "Approved Comp Off"
                        if leave_type == "comp_off"
                        else "Approved Leave"
                    )

                if reason:

                    unavailable_employees.append({
                        "employee_id": employee.id,
                        "employee_name": employee.name,
                        "reason": reason
                    })

                else:

                    available_employees.append(employee)

        available_count = len(available_employees)

        minimum_required = rule.min_staff

        # -------------------------------------
        # 8. DETERMINE STAFFING STATUS
        # -------------------------------------

        if not is_open:

            status = "CLOSED"
            coverage_gap = 0

        elif minimum_required <= 0:

            status = "COVERED"
            coverage_gap = 0

        elif available_count >= minimum_required:

            status = "COVERED"
            coverage_gap = 0

        else:

            status = "COVERAGE_GAP"

            coverage_gap = (
                minimum_required - available_count
            )

        # -------------------------------------
        # 9. BUILD RESULT
        # -------------------------------------

        results.append({
            "brand": rule.brand.name,
            "process": rule.process.name,
            "is_open": is_open,
            "status": status,
            "minimum_required": minimum_required,
            "assigned_staff": len(assigned_employees),
            "available_staff": available_count,
            "coverage_gap": coverage_gap,
            "weekly_off_policy": weekly_off_policy,
            "available_employees": [
                employee.name
                for employee in available_employees
            ],
            "unavailable_employees": unavailable_employees,
            "closed_reason": closed_reason
        })

    # -----------------------------------------
    # 10. RETURN AVAILABILITY REPORT
    # -----------------------------------------

    return {
        "date": target_date.isoformat(),
        "region": region,
        "is_public_holiday": is_public_holiday,
        "holiday_names": [
            holiday.name
            for holiday in applicable_holidays
        ],
        "total_rules": len(results),
        "coverage_gaps": sum(
            1
            for result in results
            if result["status"] == "COVERAGE_GAP"
        ),
        "results": results
    }
