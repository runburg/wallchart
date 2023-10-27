import csv
from datetime import date, timedelta
from functools import wraps
from io import TextIOWrapper

import bcrypt
import yaml
from flask import redirect, session, url_for, flash
from peewee import fn
from slugify import slugify

from wallchart.db import Department, Worker, Workplace


def max_age():
    return date.today() - timedelta(days=365)


def last_updated():
    return (
        Worker.select(fn.MAX(Worker.updated))
        .where(Worker.contract != "manual")
        .scalar()
    )


def bcryptify(password: str):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode("utf-8")


def get_current_user():
    if session.get("logged_in"):
        return Worker.get(Worker.id == session["user_id"])


def is_admin():
    return session.get("admin", False)


def login_required(f):
    @wraps(f)
    def inner(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("wallchart.login"))
        return f(*args, **kwargs)

    return inner


def parse_csv(csv_file_b):
    mapping = {}
    with open("mapping.yml") as mapping_file:
        mapping = yaml.safe_load(mapping_file)

    with TextIOWrapper(csv_file_b, encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file, delimiter=",")
        reader.fieldnames = tuple([slugify(name) for name in reader.fieldnames])

        for row in reader:
            # print(row.items())
            # department_name = mapping["mapping"].get(row["Sect Desc"], row["Sect Desc"])

            try:
                workplace_name = row["unit-in-unionware"]

                # get worker name
                worker_name = f"{row['last-name']},{row['first-name']}"
                # if row["Middle"]:
                #     worker_name += f" {row['Middle']}"

                # phone number
                if row["contact-phone"] != "":
                    phone_number = row["contact-phone"]
                elif row["alternate-contact-phone"] != "":
                    phone_number = row['alternate-contact-phone']
                else:
                    phone_number = None

                # email
                if row["email"] != "":
                    email = row["email"]
                else:
                    email = None
            except KeyError as e:
                flash(f"""
                The roster is required to have columns entitled 'unit-in-unionware', 'last-name', 'first-name', 'contact-phone', 'alternate-contact-phone', 'email'.
                Please make sure the roster has this data.\n\n
                Problem reading: {e}
                {row}"""
                      )
                return redirect(url_for("wallchart.upload_record"))



            # get worker if they exist
            worker = Worker.get_or_none(
                name=worker_name,
            )

            # The worker may be employed at multiple workplaces
            # Need to loop through the workplaces (separated by a '/'
            # And create workplaces and departments
            workplaces = []
            departments = []

            dept_id_attributes = (dept for dept in ['department', 'secondary_department'])
            for wp_name in workplace_name.split("/"):
                # get or create the workplace
                workplace, _ = Workplace.get_or_create(
                    name=wp_name.title(),
                    slug=slugify(wp_name),
                )

                # there are no department names in the current version of the roster
                if not worker:
                    department_name = f"Unknown ({wp_name})"
                else:
                    try:
                        department_name = getattr(worker, next(dept_id_attributes)).name
                    except StopIteration:
                        flash(f"""Found >2 workplaces for worker {worker.name}. This worker will only show up
                            in at most 2 departments. The department they show up in can be updated on their
                            worker page."""
                        )
                        worker.update(
                            notes=(worker.notes or '') + '\n' + f'also employed at {workplace.name}'
                        ).where(
                            Worker.id == worker.id
                        ).execute()
                        continue

                # get or create the department
                department, _ = Department.get_or_create(
                    # name=row["Job Sect Desc"].title(),
                    # slug=slugify(row["Job Sect Desc"]),
                    name=department_name.title(),
                    # workplace=workplace,
                    slug=slugify(department_name),
                    workplace=workplace.id
                )
                
                # add the new objects to our lists
                workplaces.append(workplace)
                departments.append(department)

                # populate department workplace if it hasn't been set
                #department.update(
                    #workplace=workplace.id
                #).where(
                    #Department.id == department.id,
                #).execute()

            # create worker if they don't exist yet
            primary_dept_id = departments[0].id
            workplace_id = workplaces[0].id
            
            try:
                secondary_dept_id = departments[1].id
                secondary_workplace_id = workplaces[1].id
            except IndexError:
                secondary_dept_id = None
                secondary_workplace_id = None

            if not worker:
                worker = Worker.create(
                    # name=row["Name"],
                    name=worker_name,
                    department=primary_dept_id,
                    workplace=workplace_id,
                    # default secondary_dept to None, can be changed later on
                    secondary_department=secondary_dept_id,
                    secondary_workplace=secondary_workplace_id,
                    email=email,
                    phone=phone_number,
                )
                print(f"creating new worker {worker.name} {worker.department.name} {worker.workplace.name}")

            worker.update(
                updated=date.today(),
                contract='roster',
                department=primary_dept_id,
                secondary_department=secondary_dept_id,
                workplace=workplace_id,
                secondary_workplace=secondary_workplace_id,
                active=True,
            ).where(
                Worker.id == worker.id,
            ).execute()

    Worker.update(active=False).where(Worker.updated != date.today()).execute()
