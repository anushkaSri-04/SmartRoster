
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)
from datetime import date, datetime
from sqlalchemy import func
from app.services.availability import check_date_availability
from app.extensions import db
from app.models import (
    Employee,
    Pod,
    Brand,
    Process,
    Assignment,
    OperatingRule,
    EmployeeLeave,
    PublicHoliday,
    Roster,
    RosterEntry,
    RosterEntryTask,
    Conflict
)

from app.services.roster_generator import generate_monthly_roster


main = Blueprint("main", __name__)


# -----------------------------
# DASHBOARD
# -----------------------------

@main.route("/")
def index():

    total_employees = Employee.query.count()

    active_employees = Employee.query.filter_by(
        is_active=True
    ).count()

    inactive_employees = total_employees - active_employees

    total_pods = Pod.query.count()
    total_brands = Brand.query.count()
    total_processes = Process.query.count()
    total_rosters = Roster.query.count()

    pod_statistics = (
        db.session.query(
            Pod.name,
            func.count(Employee.id)
        )
        .outerjoin(Employee, Employee.pod_id == Pod.id)
        .group_by(Pod.id, Pod.name)
        .order_by(Pod.name)
        .all()
    )

    recent_employees = (
        Employee.query
        .order_by(Employee.id.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "index.html",
        total_employees=total_employees,
        active_employees=active_employees,
        inactive_employees=inactive_employees,
        total_pods=total_pods,
        total_brands=total_brands,
        total_processes=total_processes,
        total_rosters=total_rosters,
        pod_statistics=pod_statistics,
        recent_employees=recent_employees
    )


# -----------------------------
# EMPLOYEE LIST
# -----------------------------

@main.route("/employees")
def employees():

    search = request.args.get("search", "").strip()

    query = Employee.query

    if search:
        query = query.filter(
            db.or_(
                Employee.employee_code.ilike(f"%{search}%"),
                Employee.name.ilike(f"%{search}%"),
                Employee.email.ilike(f"%{search}%")
            )
        )

    all_employees = query.order_by(
        Employee.employee_code
    ).all()

    return render_template(
        "employees/list.html",
        employees=all_employees,
        search=search
    )


# -----------------------------
# ADD EMPLOYEE
# -----------------------------

@main.route("/employees/new", methods=["GET", "POST"])
def add_employee():

    pods = Pod.query.order_by(Pod.name).all()

    if request.method == "POST":

        employee_code = request.form.get(
            "employee_code", ""
        ).strip()

        name = request.form.get("name", "").strip()

        email = request.form.get("email", "").strip()

        pod_id = request.form.get("pod_id")

        weekly_off = request.form.get("weekly_off")

        if not all([
            employee_code,
            name,
            email,
            pod_id,
            weekly_off
        ]):
            flash("Please fill in all required fields.", "danger")

            return render_template(
                "employees/form.html",
                employee=None,
                pods=pods,
                form_title="Add Employee"
            )

        if Employee.query.filter_by(
            employee_code=employee_code
        ).first():
            flash("Employee code already exists.", "danger")

            return redirect(url_for("main.add_employee"))

        if Employee.query.filter_by(email=email).first():
            flash("Email address already exists.", "danger")

            return redirect(url_for("main.add_employee"))

        employee = Employee(
            employee_code=employee_code,
            name=name,
            email=email,
            pod_id=int(pod_id),
            weekly_off=int(weekly_off),
            is_active=True
        )

        db.session.add(employee)
        db.session.commit()

        flash("Employee added successfully!", "success")

        return redirect(url_for("main.employees"))

    return render_template(
        "employees/form.html",
        employee=None,
        pods=pods,
        form_title="Add Employee"
    )


# -----------------------------
# EDIT EMPLOYEE
# -----------------------------

@main.route(
    "/employees/<int:employee_id>/edit",
    methods=["GET", "POST"]
)
def edit_employee(employee_id):

    employee = Employee.query.get_or_404(employee_id)

    pods = Pod.query.order_by(Pod.name).all()

    if request.method == "POST":

        employee_code = request.form.get(
            "employee_code", ""
        ).strip()

        name = request.form.get("name", "").strip()

        email = request.form.get("email", "").strip()

        pod_id = request.form.get("pod_id")

        weekly_off = request.form.get("weekly_off")

        if not all([
            employee_code,
            name,
            email,
            pod_id,
            weekly_off
        ]):
            flash("Please fill in all required fields.", "danger")

            return render_template(
                "employees/form.html",
                employee=employee,
                pods=pods,
                form_title="Edit Employee"
            )

        duplicate_code = Employee.query.filter(
            Employee.employee_code == employee_code,
            Employee.id != employee.id
        ).first()

        duplicate_email = Employee.query.filter(
            Employee.email == email,
            Employee.id != employee.id
        ).first()

        if duplicate_code or duplicate_email:
            flash(
                "Employee code or email already belongs to another employee.",
                "danger"
            )

            return render_template(
                "employees/form.html",
                employee=employee,
                pods=pods,
                form_title="Edit Employee"
            )

        employee.employee_code = employee_code
        employee.name = name
        employee.email = email
        employee.pod_id = int(pod_id)
        employee.weekly_off = int(weekly_off)

        db.session.commit()

        flash("Employee updated successfully!", "success")

        return redirect(url_for("main.employees"))

    return render_template(
        "employees/form.html",
        employee=employee,
        pods=pods,
        form_title="Edit Employee"
    )


# -----------------------------
# ACTIVATE / DEACTIVATE EMPLOYEE
# -----------------------------

@main.route(
    "/employees/<int:employee_id>/toggle-status",
    methods=["POST"]
)
def toggle_employee_status(employee_id):

    employee = Employee.query.get_or_404(employee_id)

    employee.is_active = not employee.is_active

    db.session.commit()

    if employee.is_active:
        flash("Employee activated successfully.", "success")
    else:
        flash("Employee deactivated successfully.", "warning")

    return redirect(url_for("main.employees"))


# -----------------------------
# HEALTH CHECK
# -----------------------------

@main.route("/health")
def health():

    try:
        db.session.execute(db.text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected"
        }, 200

    except Exception as error:

        return {
            "status": "unhealthy",
            "error": str(error)
        }, 500



# ==========================================
# POD MANAGEMENT
# ==========================================

@main.route("/pods")
def pods():

    all_pods = Pod.query.order_by(Pod.name).all()

    pod_data = []

    for pod in all_pods:

        employees = Employee.query.filter_by(
            pod_id=pod.id
        ).all()

        pod_data.append({
            "pod": pod,
            "total_employees": len(employees),
            "active_employees": sum(
                1 for emp in employees if emp.is_active
            ),
            "inactive_employees": sum(
                1 for emp in employees if not emp.is_active
            )
        })

    return render_template(
        "pods/list.html",
        pod_data=pod_data
    )


# ==========================================
# POD DETAILS
# ==========================================

@main.route("/pods/<int:pod_id>")
def pod_detail(pod_id):

    pod = Pod.query.get_or_404(pod_id)

    employees = Employee.query.filter_by(
        pod_id=pod.id
    ).order_by(Employee.employee_code).all()

    return render_template(
        "pods/detail.html",
        pod=pod,
        employees=employees
    )


# ==========================================
# ASSIGN POD LEAD
# ==========================================

@main.route(
    "/pods/<int:pod_id>/assign-lead",
    methods=["POST"]
)
def assign_pod_lead(pod_id):

    pod = Pod.query.get_or_404(pod_id)

    employee_id = request.form.get("employee_id", type=int)

    if not employee_id:
        flash("Please select an employee.", "danger")

    else:

        employee = db.session.get(Employee, employee_id)

        if not employee:
            flash("Employee not found.", "danger")

        elif employee.pod_id != pod.id:
            flash(
                "Employee does not belong to this pod.",
                "danger"
            )

        elif not employee.is_active:
            flash(
                "Inactive employees cannot be pod leads.",
                "danger"
            )

        else:
            pod.lead_employee_id = employee.id
            db.session.commit()

            flash(
                f"{employee.name} is now the lead of {pod.name}.",
                "success"
            )

    return redirect(
        url_for("main.pod_detail", pod_id=pod.id)
    )


# ==========================================
# BRAND MANAGEMENT
# ==========================================

@main.route("/brands")
def brands():

    search = request.args.get("search", "").strip()

    query = Brand.query

    if search:
        query = query.filter(
            Brand.name.ilike(f"%{search}%")
        )

    all_brands = query.order_by(Brand.name).all()

    brand_data = []

    for brand in all_brands:

        active_assignments = Assignment.query.filter_by(
            brand_id=brand.id,
            is_active=True
        ).all()

        employee_ids = {
            assignment.employee_id
            for assignment in active_assignments
        }

        brand_data.append({
            "brand": brand,
            "process_count": len({
                assignment.process_id
                for assignment in active_assignments
            }),
            "employee_count": len(employee_ids),
            "resource_type": (
                "Single Resource"
                if len(employee_ids) == 1
                else "Multi Resource"
                if len(employee_ids) > 1
                else "Unassigned"
            )
        })

    return render_template(
        "brands/list.html",
        brand_data=brand_data,
        search=search
    )


# ==========================================
# ADD BRAND
# ==========================================

@main.route("/brands/new", methods=["GET", "POST"])
def add_brand():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Brand name is required.", "danger")

            return render_template(
                "brands/form.html",
                brand=None,
                form_title="Add Brand"
            )

        existing_brand = Brand.query.filter(
            db.func.lower(Brand.name) == name.lower()
        ).first()

        if existing_brand:
            flash("A brand with this name already exists.", "danger")

            return render_template(
                "brands/form.html",
                brand=None,
                form_title="Add Brand"
            )

        brand = Brand(
            name=name,
            description=description or None,
            is_active=True
        )

        db.session.add(brand)
        db.session.commit()

        flash("Brand added successfully!", "success")

        return redirect(url_for("main.brands"))

    return render_template(
        "brands/form.html",
        brand=None,
        form_title="Add Brand"
    )


# ==========================================
# BRAND DETAILS
# ==========================================

@main.route("/brands/<int:brand_id>")
def brand_detail(brand_id):

    brand = Brand.query.get_or_404(brand_id)

    assignments = (
        Assignment.query
        .filter_by(
            brand_id=brand.id,
            is_active=True
        )
        .order_by(Assignment.process_id, Assignment.employee_id)
        .all()
    )

    process_data = {}

    for assignment in assignments:

        process = assignment.process

        if process.id not in process_data:
            process_data[process.id] = {
                "process": process,
                "employees": []
            }

        process_data[process.id]["employees"].append(
            assignment.employee
        )

    unique_employee_ids = {
        assignment.employee_id
        for assignment in assignments
    }

    employee_count = len(unique_employee_ids)

    if employee_count == 1:
        resource_type = "Single Resource"
    elif employee_count > 1:
        resource_type = "Multi Resource"
    else:
        resource_type = "Unassigned"

    return render_template(
        "brands/detail.html",
        brand=brand,
        process_data=list(process_data.values()),
        employee_count=employee_count,
        resource_type=resource_type
    )


# ==========================================
# EDIT BRAND
# ==========================================

@main.route(
    "/brands/<int:brand_id>/edit",
    methods=["GET", "POST"]
)
def edit_brand(brand_id):

    brand = Brand.query.get_or_404(brand_id)

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Brand name is required.", "danger")

            return render_template(
                "brands/form.html",
                brand=brand,
                form_title="Edit Brand"
            )

        duplicate = Brand.query.filter(
            db.func.lower(Brand.name) == name.lower(),
            Brand.id != brand.id
        ).first()

        if duplicate:
            flash("Another brand already uses this name.", "danger")

            return render_template(
                "brands/form.html",
                brand=brand,
                form_title="Edit Brand"
            )

        brand.name = name
        brand.description = description or None

        db.session.commit()

        flash("Brand updated successfully!", "success")

        return redirect(
            url_for("main.brand_detail", brand_id=brand.id)
        )

    return render_template(
        "brands/form.html",
        brand=brand,
        form_title="Edit Brand"
    )


# ==========================================
# ACTIVATE / DEACTIVATE BRAND
# ==========================================

@main.route(
    "/brands/<int:brand_id>/toggle-status",
    methods=["POST"]
)
def toggle_brand_status(brand_id):

    brand = Brand.query.get_or_404(brand_id)

    brand.is_active = not brand.is_active

    db.session.commit()

    if brand.is_active:
        flash("Brand activated successfully.", "success")
    else:
        flash("Brand deactivated successfully.", "warning")

    return redirect(url_for("main.brands"))



# ==========================================
# PROCESS MANAGEMENT
# ==========================================

@main.route("/processes")
def processes():

    all_processes = Process.query.order_by(Process.name).all()

    process_data = []

    for process in all_processes:

        active_count = Assignment.query.filter_by(
            process_id=process.id,
            is_active=True
        ).count()

        process_data.append({
            "process": process,
            "active_assignments": active_count
        })

    return render_template(
        "processes/list.html",
        process_data=process_data
    )


# ==========================================
# ADD PROCESS
# ==========================================

@main.route("/processes/new", methods=["GET", "POST"])
def add_process():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Process name is required.", "danger")

            return render_template(
                "processes/form.html",
                process=None,
                form_title="Add Process"
            )

        existing = Process.query.filter(
            db.func.lower(Process.name) == name.lower()
        ).first()

        if existing:
            flash("This process already exists.", "danger")

            return render_template(
                "processes/form.html",
                process=None,
                form_title="Add Process"
            )

        process = Process(
            name=name,
            description=description or None
        )

        db.session.add(process)
        db.session.commit()

        flash("Process added successfully!", "success")

        return redirect(url_for("main.processes"))

    return render_template(
        "processes/form.html",
        process=None,
        form_title="Add Process"
    )


# ==========================================
# EDIT PROCESS
# ==========================================

@main.route(
    "/processes/<int:process_id>/edit",
    methods=["GET", "POST"]
)
def edit_process(process_id):

    process = Process.query.get_or_404(process_id)

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Process name is required.", "danger")

            return render_template(
                "processes/form.html",
                process=process,
                form_title="Edit Process"
            )

        duplicate = Process.query.filter(
            db.func.lower(Process.name) == name.lower(),
            Process.id != process.id
        ).first()

        if duplicate:
            flash("Another process already uses this name.", "danger")

            return render_template(
                "processes/form.html",
                process=process,
                form_title="Edit Process"
            )

        process.name = name
        process.description = description or None

        db.session.commit()

        flash("Process updated successfully!", "success")

        return redirect(url_for("main.processes"))

    return render_template(
        "processes/form.html",
        process=process,
        form_title="Edit Process"
    )


# ==========================================
# ASSIGNMENT MANAGEMENT
# ==========================================

@main.route("/assignments")
def assignments():

    all_assignments = (
        Assignment.query
        .join(Brand)
        .join(Process)
        .join(Employee)
        .order_by(Brand.name, Process.name, Employee.name)
        .all()
    )

    return render_template(
        "assignments/list.html",
        assignments=all_assignments
    )


# ==========================================
# ADD ASSIGNMENT
# ==========================================

@main.route("/assignments/new", methods=["GET", "POST"])
def add_assignment():

    employees = (
        Employee.query
        .filter_by(is_active=True)
        .order_by(Employee.name)
        .all()
    )

    brands = (
        Brand.query
        .filter_by(is_active=True)
        .order_by(Brand.name)
        .all()
    )

    processes = Process.query.order_by(Process.name).all()

    if request.method == "POST":

        employee_id = request.form.get("employee_id", type=int)
        brand_id = request.form.get("brand_id", type=int)
        process_id = request.form.get("process_id", type=int)

        if not all([employee_id, brand_id, process_id]):
            flash("Please select an employee, brand and process.", "danger")

        else:

            employee = db.session.get(Employee, employee_id)
            brand = db.session.get(Brand, brand_id)
            process = db.session.get(Process, process_id)

            if not employee or not employee.is_active:
                flash("Select a valid active employee.", "danger")

            elif not brand or not brand.is_active:
                flash("Select a valid active brand.", "danger")

            elif not process:
                flash("Select a valid process.", "danger")

            else:

                existing = Assignment.query.filter_by(
                    employee_id=employee.id,
                    brand_id=brand.id,
                    process_id=process.id
                ).first()

                if existing and existing.is_active:

                    flash(
                        "This employee is already assigned to this brand and process.",
                        "warning"
                    )

                elif existing:

                    # Reactivate the existing record instead of
                    # inserting a duplicate unique combination.
                    existing.is_active = True
                    db.session.commit()

                    flash("Previous assignment reactivated!", "success")

                    return redirect(url_for("main.assignments"))

                else:

                    assignment = Assignment(
                        employee_id=employee.id,
                        brand_id=brand.id,
                        process_id=process.id,
                        is_active=True
                    )

                    db.session.add(assignment)
                    db.session.commit()

                    flash("Employee assigned successfully!", "success")

                    return redirect(url_for("main.assignments"))

        return render_template(
            "assignments/form.html",
            employees=employees,
            brands=brands,
            processes=processes
        )

    return render_template(
        "assignments/form.html",
        employees=employees,
        brands=brands,
        processes=processes
    )


# ==========================================
# ACTIVATE / DEACTIVATE ASSIGNMENT
# ==========================================

@main.route(
    "/assignments/<int:assignment_id>/toggle-status",
    methods=["POST"]
)
def toggle_assignment_status(assignment_id):

    assignment = Assignment.query.get_or_404(assignment_id)

    if not assignment.is_active:

        if not assignment.employee.is_active:
            flash(
                "Cannot activate an assignment for an inactive employee.",
                "danger"
            )
            return redirect(url_for("main.assignments"))

        if not assignment.brand.is_active:
            flash(
                "Cannot activate an assignment for an inactive brand.",
                "danger"
            )
            return redirect(url_for("main.assignments"))

    assignment.is_active = not assignment.is_active

    db.session.commit()

    if assignment.is_active:
        flash("Assignment activated successfully.", "success")
    else:
        flash("Assignment deactivated successfully.", "warning")

    return redirect(url_for("main.assignments"))


# ==========================================
# OPERATING RULES MANAGEMENT
# ==========================================

WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
]

WEEKLY_OFF_POLICIES = {
    "require_backup",
    "close_process"
}


@main.route("/operating-rules")
def operating_rules():

    rules = (
        OperatingRule.query
        .join(Brand)
        .join(Process)
        .order_by(Brand.name, Process.name)
        .all()
    )

    return render_template(
        "operating_rules/list.html",
        rules=rules,
        weekdays=WEEKDAYS
    )


# ==========================================
# ADD OPERATING RULE
# ==========================================

@main.route(
    "/operating-rules/new",
    methods=["GET", "POST"]
)
def add_operating_rule():

    brands = Brand.query.filter_by(
        is_active=True
    ).order_by(Brand.name).all()

    processes = Process.query.order_by(
        Process.name
    ).all()

    if request.method == "POST":

        brand_id = request.form.get("brand_id", type=int)
        process_id = request.form.get("process_id", type=int)

        working_days = request.form.getlist("working_days")

        holidays_open = request.form.get("holidays_open") == "yes"

        min_staff = request.form.get("min_staff", type=int)
        weekly_off_policy = request.form.get(
            "weekly_off_policy",
            "require_backup"
        ).strip()

        if weekly_off_policy not in WEEKLY_OFF_POLICIES:
            flash("Please select a valid weekly-off staffing policy.", "danger")

        elif not brand_id or not process_id:
            flash("Please select a brand and process.", "danger")

        elif min_staff is None or min_staff < 0:
            flash("Minimum staffing must be zero or greater.", "danger")

        elif not working_days:
            flash("Select at least one working day.", "danger")

        else:

            brand = db.session.get(Brand, brand_id)
            process = db.session.get(Process, process_id)

            if not brand or not brand.is_active:
                flash("Select a valid active brand.", "danger")

            elif not process:
                flash("Select a valid process.", "danger")

            else:

                try:
                    selected_days = sorted(set(
                        int(day) for day in working_days
                    ))

                    if any(day < 0 or day > 6 for day in selected_days):
                        raise ValueError

                except ValueError:
                    flash("Invalid working day selection.", "danger")

                else:

                    existing = OperatingRule.query.filter_by(
                        brand_id=brand_id,
                        process_id=process_id
                    ).first()

                    if existing:
                        flash(
                            "An operating rule already exists for this brand and process. Edit the existing rule instead.",
                            "warning"
                        )

                    else:

                        rule = OperatingRule(
                            brand_id=brand_id,
                            process_id=process_id,
                            working_days=selected_days,
                            holidays_open=holidays_open,
                            min_staff=min_staff,
                            weekly_off_policy=weekly_off_policy
                        )

                        db.session.add(rule)
                        db.session.commit()

                        flash(
                            "Operating rule created successfully!",
                            "success"
                        )

                        return redirect(
                            url_for("main.operating_rules")
                        )

        return render_template(
            "operating_rules/form.html",
            rule=None,
            brands=brands,
            processes=processes,
            weekdays=WEEKDAYS,
            form_title="Add Operating Rule"
        )

    return render_template(
        "operating_rules/form.html",
        rule=None,
        brands=brands,
        processes=processes,
        weekdays=WEEKDAYS,
        form_title="Add Operating Rule"
    )


# ==========================================
# EDIT OPERATING RULE
# ==========================================

@main.route(
    "/operating-rules/<int:rule_id>/edit",
    methods=["GET", "POST"]
)
def edit_operating_rule(rule_id):

    rule = OperatingRule.query.get_or_404(rule_id)

    brands = Brand.query.filter_by(
        is_active=True
    ).order_by(Brand.name).all()

    processes = Process.query.order_by(
        Process.name
    ).all()

    if request.method == "POST":

        working_days = request.form.getlist("working_days")

        holidays_open = request.form.get("holidays_open") == "yes"

        min_staff = request.form.get("min_staff", type=int)
        weekly_off_policy = request.form.get(
            "weekly_off_policy",
            rule.weekly_off_policy or "require_backup"
        ).strip()

        if weekly_off_policy not in WEEKLY_OFF_POLICIES:
            flash("Please select a valid weekly-off staffing policy.", "danger")

        elif min_staff is None or min_staff < 0:
            flash("Minimum staffing must be zero or greater.", "danger")

        elif not working_days:
            flash("Select at least one working day.", "danger")

        else:

            try:
                selected_days = sorted(set(
                    int(day) for day in working_days
                ))

                if any(day < 0 or day > 6 for day in selected_days):
                    raise ValueError

            except ValueError:
                flash("Invalid working day selection.", "danger")

            else:

                rule.working_days = selected_days
                rule.holidays_open = holidays_open
                rule.min_staff = min_staff
                rule.weekly_off_policy = weekly_off_policy

                db.session.commit()

                flash(
                    "Operating rule updated successfully!",
                    "success"
                )

                return redirect(
                    url_for("main.operating_rules")
                )

        return render_template(
            "operating_rules/form.html",
            rule=rule,
            brands=brands,
            processes=processes,
            weekdays=WEEKDAYS,
            form_title="Edit Operating Rule"
        )

    return render_template(
        "operating_rules/form.html",
        rule=rule,
        brands=brands,
        processes=processes,
        weekdays=WEEKDAYS,
        form_title="Edit Operating Rule"
    )


@main.route("/leaves")
def leaves():
    leave_records = (
        EmployeeLeave.query
        .join(Employee)
        .order_by(EmployeeLeave.start_date.desc())
        .all()
    )

    return render_template(
        "leaves/list.html",
        leaves=leave_records
    )


@main.route("/leaves/new", methods=["GET", "POST"])
def add_leave():

    employees = Employee.query.filter_by(is_active=True).order_by(
        Employee.name
    ).all()

    if request.method == "POST":
        employee_id = request.form.get("employee_id")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        leave_type = request.form.get("leave_type")

        if not all([employee_id, start_date, end_date, leave_type]):
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("main.add_leave"))

        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            employee_id = int(employee_id)
        except (ValueError, TypeError):
            flash("Invalid employee or date.", "danger")
            return redirect(url_for("main.add_leave"))

        if end < start:
            flash("End date cannot be before start date.", "danger")
            return redirect(url_for("main.add_leave"))

        if leave_type not in ["planned_leave", "sick_leave", "comp_off"]:
            flash("Invalid leave type.", "danger")
            return redirect(url_for("main.add_leave"))

        employee = db.session.get(Employee, employee_id)

        if not employee or not employee.is_active:
            flash("Select a valid active employee.", "danger")
            return redirect(url_for("main.add_leave"))

        # Prevent overlapping non-rejected leave records.
        overlapping_leave = EmployeeLeave.query.filter(
            EmployeeLeave.employee_id == employee_id,
            EmployeeLeave.status != "rejected",
            EmployeeLeave.start_date <= end,
            EmployeeLeave.end_date >= start
        ).first()

        if overlapping_leave:
            flash(
                "This employee already has a leave record overlapping these dates.",
                "danger"
            )
            return redirect(url_for("main.add_leave"))

        leave = EmployeeLeave(
            employee_id=employee_id,
            start_date=start,
            end_date=end,
            leave_type=leave_type,
            status="pending"
        )

        db.session.add(leave)
        db.session.commit()

        flash("Leave request submitted successfully.", "success")
        return redirect(url_for("main.leaves"))

    return render_template(
        "leaves/form.html",
        employees=employees
    )


@main.route("/leaves/<int:leave_id>/status/<string:status>", methods=["POST"])
def update_leave_status(leave_id, status):

    if status not in ["approved", "rejected"]:
        flash("Invalid leave status.", "danger")
        return redirect(url_for("main.leaves"))

    leave = db.session.get(EmployeeLeave, leave_id)

    if not leave:
        flash("Leave record not found.", "danger")
        return redirect(url_for("main.leaves"))

    if leave.status != "pending":
        flash("Only pending leave requests can be updated.", "warning")
        return redirect(url_for("main.leaves"))

    leave.status = status
    db.session.commit()

    flash(f"Leave request {status}.", "success")
    return redirect(url_for("main.leaves"))



@main.route("/public-holidays")
def public_holidays():
    holidays = PublicHoliday.query.order_by(
        PublicHoliday.holiday_date.asc()
    ).all()

    return render_template(
        "public_holidays/list.html",
        holidays=holidays
    )


@main.route("/public-holidays/new", methods=["GET", "POST"])
def add_public_holiday():

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        holiday_date = request.form.get("holiday_date", "").strip()
        region = request.form.get("region", "").strip() or None

        if not name or not holiday_date:
            flash("Holiday name and date are required.", "danger")
            return redirect(url_for("main.add_public_holiday"))

        try:
            parsed_date = date.fromisoformat(holiday_date)
        except ValueError:
            flash("Please enter a valid holiday date.", "danger")
            return redirect(url_for("main.add_public_holiday"))

        duplicate_query = PublicHoliday.query.filter(
            PublicHoliday.holiday_date == parsed_date
        )

        if region is None:
            duplicate_query = duplicate_query.filter(
                PublicHoliday.region.is_(None)
            )
        else:
            duplicate_query = duplicate_query.filter(
                PublicHoliday.region == region
            )

        if duplicate_query.first():
            flash(
                "A holiday already exists for this date and region.",
                "warning"
            )
            return redirect(url_for("main.add_public_holiday"))

        holiday = PublicHoliday(
            name=name,
            holiday_date=parsed_date,
            region=region
        )

        db.session.add(holiday)
        db.session.commit()

        flash("Public holiday added successfully.", "success")
        return redirect(url_for("main.public_holidays"))

    return render_template("public_holidays/form.html")


@main.route(
    "/public-holidays/<int:holiday_id>/edit",
    methods=["GET", "POST"]
)
def edit_public_holiday(holiday_id):

    holiday = db.session.get(PublicHoliday, holiday_id)

    if not holiday:
        flash("Holiday not found.", "danger")
        return redirect(url_for("main.public_holidays"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        holiday_date = request.form.get("holiday_date", "").strip()
        region = request.form.get("region", "").strip() or None

        if not name or not holiday_date:
            flash("Holiday name and date are required.", "danger")
            return redirect(
                url_for("main.edit_public_holiday", holiday_id=holiday.id)
            )

        try:
            parsed_date = date.fromisoformat(holiday_date)
        except ValueError:
            flash("Please enter a valid holiday date.", "danger")
            return redirect(
                url_for("main.edit_public_holiday", holiday_id=holiday.id)
            )

        duplicate_query = PublicHoliday.query.filter(
            PublicHoliday.holiday_date == parsed_date,
            PublicHoliday.id != holiday.id
        )

        if region is None:
            duplicate_query = duplicate_query.filter(
                PublicHoliday.region.is_(None)
            )
        else:
            duplicate_query = duplicate_query.filter(
                PublicHoliday.region == region
            )

        if duplicate_query.first():
            flash(
                "Another holiday already exists for this date and region.",
                "warning"
            )
            return redirect(
                url_for("main.edit_public_holiday", holiday_id=holiday.id)
            )

        holiday.name = name
        holiday.holiday_date = parsed_date
        holiday.region = region

        db.session.commit()

        flash("Public holiday updated successfully.", "success")
        return redirect(url_for("main.public_holidays"))

    return render_template(
        "public_holidays/form.html",
        holiday=holiday
    )


@main.route(
    "/public-holidays/<int:holiday_id>/delete",
    methods=["POST"]
)
def delete_public_holiday(holiday_id):

    holiday = db.session.get(PublicHoliday, holiday_id)

    if not holiday:
        flash("Holiday not found.", "danger")
        return redirect(url_for("main.public_holidays"))

    db.session.delete(holiday)
    db.session.commit()

    flash("Public holiday deleted successfully.", "success")
    return redirect(url_for("main.public_holidays"))



@main.route("/availability")
def availability_dashboard():

    selected_date = request.args.get("date", date.today().isoformat())
    region = request.args.get("region", "Maharashtra").strip()

    try:
        parsed_date = date.fromisoformat(selected_date)
    except ValueError:
        flash("Invalid date selected.", "danger")
        parsed_date = date.today()
        selected_date = parsed_date.isoformat()

    report = check_date_availability(
        target_date=parsed_date,
        region=region or None
    )

    results = report["results"]

    summary = {
        "total": len(results),
        "covered": sum(
            1 for item in results if item["status"] == "COVERED"
        ),
        "closed": sum(
            1 for item in results if item["status"] == "CLOSED"
        ),
        "gaps": sum(
            1 for item in results if item["status"] == "COVERAGE_GAP"
        )
    }

    return render_template(
        "availability/dashboard.html",
        report=report,
        summary=summary,
        selected_date=selected_date,
        region=region
    )



@main.route("/rosters/generate", methods=["GET", "POST"])
def generate_roster():

    if request.method == "POST":

        try:
            month = int(request.form.get("month"))
            year = int(request.form.get("year"))
            region = request.form.get("region", "").strip() or None

            result = generate_monthly_roster(
                month=month,
                year=year,
                region=region
            )

            flash(
                f"Roster generated successfully. "
                f"{result['allocated_tasks']} tasks allocated. "
                f"{result['coverage_gaps']} coverage gaps found.",
                "success"
            )

            return redirect(
                url_for(
                    "main.roster_detail",
                    roster_id=result["roster_id"]
                )
            )

        except (ValueError, TypeError) as error:
            flash(str(error), "danger")

        except Exception:
            db.session.rollback()
            flash(
                "An unexpected error occurred while generating the roster.",
                "danger"
            )

    return render_template("rosters/generate.html")


@main.route("/rosters/<int:roster_id>")
def roster_detail(roster_id):

    roster = db.session.get(Roster, roster_id)

    if not roster:
        flash("Roster not found.", "danger")
        return redirect(url_for("main.generate_roster"))

    entries = (
        RosterEntry.query
        .filter_by(roster_id=roster.id)
        .order_by(
            RosterEntry.work_date,
            RosterEntry.employee_id
        )
        .all()
    )

    conflicts = Conflict.query.filter_by(
        roster_id=roster.id
    ).order_by(Conflict.conflict_date).all()

    return render_template(
        "rosters/detail.html",
        roster=roster,
        entries=entries,
        conflicts=conflicts
    )

# ==========================================
# MANUAL ROSTER TASK REASSIGNMENT
# ==========================================

def revalidate_process_coverage(
    roster_id,
    brand_id,
    process_id,
    work_date
):
    """Recalculate coverage for one roster, process and date."""

    rule = OperatingRule.query.filter_by(
        brand_id=brand_id,
        process_id=process_id
    ).first()

    if not rule:
        return {
            "valid": False,
            "message": "Operating rule not found.",
            "coverage_gap": 0
        }

    assigned_employees = (
        Employee.query
        .join(Assignment, Assignment.employee_id == Employee.id)
        .filter(
            Assignment.brand_id == brand_id,
            Assignment.process_id == process_id,
            Assignment.is_active.is_(True),
            Employee.is_active.is_(True)
        )
        .distinct()
        .all()
    )

    assigned_employee_ids = {employee.id for employee in assigned_employees}

    # Count only employees with an active assignment and a working entry.
    allocated_rows = (
        db.session.query(RosterEntry.employee_id)
        .join(
            RosterEntryTask,
            RosterEntryTask.roster_entry_id == RosterEntry.id
        )
        .filter(
            RosterEntry.roster_id == roster_id,
            RosterEntry.work_date == work_date,
            RosterEntry.status == "working",
            RosterEntryTask.brand_id == brand_id,
            RosterEntryTask.process_id == process_id
        )
        .distinct()
        .all()
    )

    allocated_employee_ids = {row[0] for row in allocated_rows}
    valid_allocated_ids = allocated_employee_ids & assigned_employee_ids
    allocated_count = len(valid_allocated_ids)

    all_assigned_on_weekly_off = (
        bool(assigned_employees)
        and all(
            employee.weekly_off == work_date.weekday()
            for employee in assigned_employees
        )
    )

    process_closed = (
        rule.weekly_off_policy == "close_process"
        and all_assigned_on_weekly_off
    )

    coverage_gap = (
        not process_closed
        and allocated_count < rule.min_staff
    )

    # Only touch conflicts for this exact roster/brand/process/date.
    unresolved_conflicts = Conflict.query.filter_by(
        roster_id=roster_id,
        brand_id=brand_id,
        process_id=process_id,
        conflict_date=work_date,
        is_resolved=False
    ).order_by(Conflict.id).all()

    if coverage_gap:
        message = (
            f"Minimum staffing requirement is {rule.min_staff}, "
            f"but only {allocated_count} valid employee(s) "
            f"are allocated to this process."
        )

        if unresolved_conflicts:
            primary_conflict = unresolved_conflicts[0]
            primary_conflict.message = message
            primary_conflict.severity = "high"

            # Avoid multiple active conflict records for the same issue.
            for duplicate in unresolved_conflicts[1:]:
                duplicate.is_resolved = True
        else:
            db.session.add(Conflict(
                roster_id=roster_id,
                brand_id=brand_id,
                process_id=process_id,
                conflict_date=work_date,
                severity="high",
                message=message,
                is_resolved=False
            ))
    else:
        for conflict in unresolved_conflicts:
            conflict.is_resolved = True

    return {
        "valid": not coverage_gap,
        "process_closed": process_closed,
        "minimum_required": rule.min_staff,
        "allocated_count": allocated_count,
        "coverage_gap": max(0, rule.min_staff - allocated_count),
        "message": (
            "Coverage gap detected."
            if coverage_gap
            else "Coverage requirement satisfied."
        )
    }


@main.route(
    "/roster-tasks/<int:task_id>/edit",
    methods=["GET", "POST"]
)
def edit_roster_task(task_id):
    task = RosterEntryTask.query.get_or_404(task_id)
    current_entry = task.roster_entry
    roster = current_entry.roster
    work_date = current_entry.work_date

    if roster.status != "draft":
        flash("Only draft rosters can be manually edited.", "danger")
        return redirect(url_for("main.roster_detail", roster_id=roster.id))

    rule = OperatingRule.query.filter_by(
        brand_id=task.brand_id,
        process_id=task.process_id
    ).first()

    if not rule:
        flash("No operating rule exists for this brand and process.", "danger")
        return redirect(url_for("main.roster_detail", roster_id=roster.id))

    # Employees must have an active assignment to this exact process.
    eligible_employee_ids = {
        row[0] for row in (
            db.session.query(Assignment.employee_id)
            .join(Employee, Employee.id == Assignment.employee_id)
            .filter(
                Assignment.brand_id == task.brand_id,
                Assignment.process_id == task.process_id,
                Assignment.is_active.is_(True),
                Employee.is_active.is_(True)
            )
            .all()
        )
    }

    eligible_entries = (
        RosterEntry.query
        .join(Employee, Employee.id == RosterEntry.employee_id)
        .filter(
            RosterEntry.roster_id == roster.id,
            RosterEntry.work_date == work_date,
            RosterEntry.status == "working",
            RosterEntry.employee_id.in_(eligible_employee_ids)
        )
        .order_by(Employee.name)
        .all()
    ) if eligible_employee_ids else []

    if request.method == "POST":
        target_entry_id = request.form.get("target_entry_id", type=int)
        target_entry = (
            db.session.get(RosterEntry, target_entry_id)
            if target_entry_id else None
        )

        if not target_entry:
            flash("Please select a valid employee.", "danger")
        elif target_entry.roster_id != roster.id:
            flash("Selected employee belongs to another roster.", "danger")
        elif target_entry.work_date != work_date:
            flash("The selected employee entry has a different date.", "danger")
        elif target_entry.status != "working":
            flash("The selected employee is not available on this date.", "danger")
        elif target_entry.employee_id not in eligible_employee_ids:
            flash(
                "This employee is not actively assigned to this brand and process.",
                "danger"
            )
        elif work_date.weekday() not in (rule.working_days or []):
            flash("This process is not scheduled to operate on this weekday.", "danger")
        else:
            duplicate_task = RosterEntryTask.query.filter_by(
                roster_entry_id=target_entry.id,
                brand_id=task.brand_id,
                process_id=task.process_id
            ).first()

            if duplicate_task and duplicate_task.id != task.id:
                flash(
                    "This employee already has this process assigned on this date.",
                    "warning"
                )
            elif target_entry.id == current_entry.id:
                flash("The task is already assigned to this employee.", "info")
            else:
                try:
                    task.roster_entry_id = target_entry.id
                    db.session.flush()

                    validation_result = revalidate_process_coverage(
                        roster_id=roster.id,
                        brand_id=task.brand_id,
                        process_id=task.process_id,
                        work_date=work_date
                    )

                    db.session.commit()

                    if validation_result["valid"]:
                        flash(
                            "Task reassigned successfully. Coverage requirement is satisfied.",
                            "success"
                        )
                    else:
                        flash(
                            "Task reassigned, but a coverage gap remains. Check the conflicts section.",
                            "warning"
                        )

                    return redirect(
                        url_for("main.roster_detail", roster_id=roster.id)
                    )
                except Exception:
                    db.session.rollback()
                    raise

    return render_template(
        "rosters/edit_task.html",
        task=task,
        roster=roster,
        eligible_entries=eligible_entries,
        current_entry=current_entry
    )
