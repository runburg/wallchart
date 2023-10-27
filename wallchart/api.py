from flask import Blueprint, jsonify
from playhouse.flask_utils import get_object_or_404

from wallchart.db import Department, Participation, Workplace, Worker
from wallchart.util import login_required

api = Blueprint("api", __name__, url_prefix="/api")


@api.route("/workers")
@login_required
def api_workers():
    return jsonify(
        list(
            Worker.select(
                Worker,
                Department.slug.alias("department_slug"),
                Department.name.alias("department_name"),
            )
            .join(Department, on=Worker.department)
            .dicts()
        )
    )


@api.route("/worker")
@api.route("/worker/<int:worker_id>")
@login_required
def api_worker(worker_id):
    workers = (
        Worker.select(
            Worker,
            Department.slug.alias("department_slug"),
            Department.name.alias("department_name"),
        )
        .join(Department, on=Worker.department)
        .dicts()
    )

    worker = get_object_or_404(workers, (Worker.id == worker_id))
    return jsonify(worker)


@api.route("/participation")
@login_required
def api_participation():
    return jsonify(
        list(
            Participation.select(Participation, Worker.department.id)
            .join(Worker, on=Participation.worker)
            .dicts()
        )
    )


@api.route("/departments")
@login_required
def api_departments():
    return jsonify(list(Department.select().dicts()))


@api.route("/workplaces")
@login_required
def api_workplaces():
    return jsonify(list(Workplace.select().dicts()))
