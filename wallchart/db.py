from datetime import date

from flask import Blueprint, current_app
from peewee import (
    AutoField,
    BooleanField,
    CharField,
    DateField,
    ForeignKeyField,
    IntegerField,
    TextField,
    CompositeKey,
)

from wallchart import db_wrapper

db = Blueprint("db", __name__)


class Workplace(db_wrapper.Model):
    id = AutoField()
    name = CharField(unique=True)
    slug = CharField()


class Department(db_wrapper.Model):
    id = AutoField()
    name = CharField()
    slug = CharField()
    alias = CharField(null=True)
    workplace = ForeignKeyField(Workplace, backref="departments", null=True)


class Worker(db_wrapper.Model):
    id = AutoField()
    name = CharField()
    preferred_name = CharField(null=True)
    pronouns = CharField(null=True)
    email = CharField(null=True)
    phone = IntegerField(null=True)
    notes = TextField(null=True)
    contract = CharField(null=True)
    workplace = ForeignKeyField(Workplace, null=True)
    secondary_workplace = ForeignKeyField(Workplace, null=True)
    department = ForeignKeyField(Department, backref="workers1", null=True)
    secondary_department = ForeignKeyField(Department, backref="workers2", null=True)
    workplace_chair_id = ForeignKeyField(Workplace, field=Workplace.id, backref="chairs", null=True)
    dept_chair_id = ForeignKeyField(
        Department, field=Department.id, backref="stewards", null=True
    )
    active = BooleanField(default=True)
    added = DateField(default=date.today)
    updated = DateField(default=date.today)
    password = CharField(null=True)

    class Meta:
        indexes = ((("name", "workplace", "secondary_workplace", "department", "secondary_department"), True),)


class StructureTest(db_wrapper.Model):
    id = AutoField()
    name = CharField(unique=True)
    description = TextField()
    active = BooleanField(default=True)
    added = DateField(default=date.today)

# class StructureTestWorkplaceRelation(db_wrapper.Model):
#     workplace = ForeignKeyField(Workplace)
#     structure_test = ForeignKeyField(StructureTest)

#     class Meta:
#         primary_key = CompositeKey('structure_test', 'workplace')
    

class Participation(db_wrapper.Model):
    worker = ForeignKeyField(Worker, field="id")
    structure_test = ForeignKeyField(StructureTest)
    added = DateField(default=date.today)

    class Meta:
        indexes = ((("worker", "structure_test"), True),)


def create_tables():
    with db_wrapper.database.connection_context():
        db_wrapper.database.create_tables(
            [Workplace, Department, Worker, StructureTest, Participation]
        )
        department, _ = Department.get_or_create(
            id=0,
            name="Admin",
            slug="admin",
        )
        structure_test, _ = StructureTest.get_or_create(
                name="test",
                description="created on initialization of db. feel free to delete :)",
                active=False,
        )

def close():
    if not db_wrapper.database.is_closed():
        db_wrapper.database.close()
