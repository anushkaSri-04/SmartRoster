
from datetime import date

from app import create_app
from app.extensions import db
from app.models import (
    Pod,
    Employee,
    Brand,
    Process,
    Assignment,
    OperatingRule,
    PublicHoliday
)


# =========================================
# 1. SAMPLE DATA
# =========================================

POD_NAMES = [
    "Pod Alpha",
    "Pod Beta",
    "Pod Gamma",
    "Pod Delta",
    "Pod Epsilon"
]


EMPLOYEE_NAMES = [
    "Aarav Sharma", "Priya Mehta", "Rahul Verma",
    "Sneha Patel", "Arjun Singh", "Kavya Nair",
    "Rohan Gupta", "Ananya Reddy", "Aditya Joshi",
    "Isha Kapoor", "Vikram Shah", "Meera Iyer",
    "Karan Malhotra", "Diya Desai", "Siddharth Rao",
    "Pooja Mishra", "Nikhil Jain", "Riya Das",
    "Varun Khanna", "Aditi Kulkarni", "Manav Sethi",
    "Neha Bansal", "Yash Thakur", "Simran Kaur",
    "Dev Malhotra", "Tanya Roy", "Kabir Anand",
    "Sana Sheikh", "Ishaan Bose", "Avni Chawla"
]


BRAND_NAMES = [
    "EcoWear", "UrbanNest", "StyleHub", "GlowTheory",
    "PureLiving", "TrendCraft", "FitFuel", "HomeBliss",
    "SkinNova", "DailyRoots", "FreshKart", "LuxeLane",
    "NatureNest", "TechTrove", "VelvetVibe", "GreenBasket",
    "AuraLiving", "ModernMuse", "WellnessWay", "CraftCorner",
    "UrbanBloom", "PureThreads", "NovaStyle", "EarthEssence",
    "CloudNine", "BoldBasics", "TheGoodStore",
    "EverGlow", "DailyDose", "PrimeLiving"
]


PROCESS_NAMES = [
    "Customer Support",
    "Abandoned Cart Conversions",
    "Retention",
    "Non-Delivery Report",
    "Returns Management"
]


# =========================================
# 2. PROCESS OPERATING RULES
# =========================================

PROCESS_RULES = {
    "Customer Support": {
        "working_days": [0, 1, 2, 3, 4, 5, 6],
        "holidays_open": True,
        "min_staff": 1
    },

    "Abandoned Cart Conversions": {
        "working_days": [0, 1, 2, 3, 4, 5],
        "holidays_open": False,
        "min_staff": 1
    },

    "Retention": {
        "working_days": [0, 1, 2, 3, 4, 5],
        "holidays_open": False,
        "min_staff": 1
    },

    "Non-Delivery Report": {
        "working_days": [0, 1, 2, 3, 4, 5, 6],
        "holidays_open": False,
        "min_staff": 1
    },

    "Returns Management": {
        "working_days": [0, 1, 2, 3, 4, 5],
        "holidays_open": False,
        "min_staff": 1
    }
}


# =========================================
# 3. MULTI-RESOURCE BRAND ASSIGNMENTS
# =========================================
# Format:
# Brand number: [(employee number, process number)]
#
# Employee and process numbers start from 1.

MULTI_RESOURCE_ASSIGNMENTS = {
    25: [(25, 1), (1, 1)],

    26: [(26, 1), (2, 5)],

    27: [(27, 2), (3, 4), (4, 4)],

    28: [(28, 3), (4, 1)],

    29: [(29, 4), (5, 5)],

    30: [(30, 5), (6, 5)]
}


# =========================================
# 4. HELPER FUNCTION
# =========================================

def get_or_create(model, filters, defaults=None):

    record = model.query.filter_by(**filters).first()

    if record:
        return record, False

    record = model(**(defaults or {}), **filters)

    db.session.add(record)

    return record, True


# =========================================
# 5. MAIN SEED FUNCTION
# =========================================

def seed_database():

    app = create_app()

    with app.app_context():

        try:

            print("\nStarting SmartRoster database seeding...")

            # ---------------------------------
            # CREATE PODS
            # ---------------------------------

            pods = {}

            for pod_name in POD_NAMES:

                pod, created = get_or_create(
                    Pod,
                    {"name": pod_name}
                )

                pods[pod_name] = pod

            db.session.flush()

            print("Pods created/verified:", len(pods))


            # ---------------------------------
            # CREATE EMPLOYEES
            # ---------------------------------

            employees = {}

            for index, employee_name in enumerate(
                EMPLOYEE_NAMES,
                start=1
            ):

                pod_index = (index - 1) // 6

                pod = pods[POD_NAMES[pod_index]]

                employee_code = f"EMP{index:03d}"

                employee, created = get_or_create(
                    Employee,
                    {"employee_code": employee_code},
                    {
                        "name": employee_name,
                        "email": (
                            f"employee{index:03d}"
                            "@smartroster.demo"
                        ),
                        "pod_id": pod.id,
                        "weekly_off": (index - 1) % 7,
                        "is_active": True
                    }
                )

                # Keep existing employee records aligned
                # with this sample dataset.
                employee.name = employee_name
                employee.pod_id = pod.id
                employee.weekly_off = (index - 1) % 7
                employee.is_active = True

                employees[index] = employee

            db.session.flush()

            print("Employees created/verified:", len(employees))


            # ---------------------------------
            # ASSIGN POD LEADS
            # ---------------------------------

            for pod_index, pod_name in enumerate(
                POD_NAMES
            ):

                lead_employee_number = (
                    pod_index * 6
                ) + 1

                pods[pod_name].lead_employee_id = (
                    employees[lead_employee_number].id
                )

            db.session.flush()

            print("Pod leads assigned: 5")


            # ---------------------------------
            # CREATE PROCESSES
            # ---------------------------------

            processes = {}

            for process_name in PROCESS_NAMES:

                process, created = get_or_create(
                    Process,
                    {"name": process_name}
                )

                processes[process_name] = process

            db.session.flush()

            print("Processes created/verified:", len(processes))


            # ---------------------------------
            # CREATE BRANDS
            # ---------------------------------

            brands = {}

            for brand_name in BRAND_NAMES:

                brand, created = get_or_create(
                    Brand,
                    {"name": brand_name},
                    {
                        "description": (
                            f"Sample D2C brand: {brand_name}"
                        ),
                        "is_active": True
                    }
                )

                brands[brand_name] = brand

            db.session.flush()

            print("Brands created/verified:", len(brands))


            # ---------------------------------
            # GENERATE SINGLE-RESOURCE
            # BRAND ASSIGNMENTS
            # ---------------------------------

            assignment_pairs = set()

            # First 24 brands have one
            # dedicated employee each.

            for brand_number in range(1, 25):

                employee = employees[brand_number]

                brand = brands[BRAND_NAMES[brand_number - 1]]

                process_one = PROCESS_NAMES[
                    (brand_number - 1) % 5
                ]

                process_two = PROCESS_NAMES[
                    brand_number % 5
                ]

                assignment_pairs.add((
                    employee.id,
                    brand.id,
                    processes[process_one].id
                ))

                assignment_pairs.add((
                    employee.id,
                    brand.id,
                    processes[process_two].id
                ))


            # ---------------------------------
            # GENERATE MULTI-RESOURCE
            # BRAND ASSIGNMENTS
            # ---------------------------------

            for brand_number, assignments in (
                MULTI_RESOURCE_ASSIGNMENTS.items()
            ):

                brand = brands[BRAND_NAMES[brand_number - 1]]

                for employee_number, process_number in assignments:

                    employee = employees[employee_number]

                    process = processes[
                        PROCESS_NAMES[process_number - 1]
                    ]

                    assignment_pairs.add((
                        employee.id,
                        brand.id,
                        process.id
                    ))


            # ---------------------------------
            # SAVE ASSIGNMENTS
            # ---------------------------------

            for employee_id, brand_id, process_id in (
                assignment_pairs
            ):

                get_or_create(
                    Assignment,
                    {
                        "employee_id": employee_id,
                        "brand_id": brand_id,
                        "process_id": process_id
                    },
                    {
                        "is_active": True
                    }
                )

            db.session.flush()

            print(
                "Assignments created/verified:",
                len(assignment_pairs)
            )


            
            # ---------------------------------
            # CREATE OPERATING RULES
            # ---------------------------------

            brand_process_pairs = {
                (brand_id, process_id)
                for _, brand_id, process_id in assignment_pairs
            }

            for brand_id, process_id in brand_process_pairs:

                process = db.session.get(Process, process_id)

                rule_data = PROCESS_RULES[process.name]

                # Demonstrate a process requiring 2 employees.
                min_staff = rule_data["min_staff"]

                if (
                    brand_id == brands[BRAND_NAMES[26]].id
                    and process.name == "Non-Delivery Report"
                ):
                    min_staff = 2

                rule, created = get_or_create(
                    OperatingRule,
                    {
                        "brand_id": brand_id,
                        "process_id": process_id
                    },
                    {
                        "working_days": rule_data["working_days"],
                        "holidays_open": rule_data["holidays_open"],
                        "min_staff": min_staff
                    }
                )

                # Keep existing rules synchronized on reruns.
                rule.working_days = rule_data["working_days"]
                rule.holidays_open = rule_data["holidays_open"]
                rule.min_staff = min_staff

            db.session.flush()

            print(
                "Operating rules created/verified:",
                len(brand_process_pairs)
            )



            # ---------------------------------
            # CREATE PUBLIC HOLIDAYS
            # ---------------------------------

            holidays = [
                ("Republic Day", date(2027, 1, 26)),
                ("Independence Day", date(2027, 8, 15)),
                ("Gandhi Jayanti", date(2027, 10, 2))
            ]

            for holiday_name, holiday_date in holidays:

                get_or_create(
                    PublicHoliday,
                    {
                        "holiday_date": holiday_date,
                        "region": "Maharashtra"
                    },
                    {
                        "name": holiday_name
                    }
                )

            # ---------------------------------
            # COMMIT TRANSACTION
            # ---------------------------------

            db.session.commit()

            print("\n================================")
            print("SMARTROSTER SEEDING SUCCESSFUL")
            print("================================")

            print("Employees:", Employee.query.count())
            print("Pods:", Pod.query.count())
            print("Brands:", Brand.query.count())
            print("Processes:", Process.query.count())
            print("Assignments:", Assignment.query.count())
            print("Operating Rules:", OperatingRule.query.count())
            print("Public Holidays:", PublicHoliday.query.count())

            print("================================\n")

        except Exception as error:

            db.session.rollback()

            print("\nSEEDING FAILED")
            print("Error:", error)

            raise


if __name__ == "__main__":
    seed_database()
