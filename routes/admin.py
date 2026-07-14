from flask import Blueprint, abort, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models import Machine, db

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/", methods=["GET"])
@login_required
def index():
    return redirect(url_for("admin.machine_list"))


@admin_bp.route("/machines", methods=["GET", "POST"])
@login_required
def machine_list():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        status = request.form.get("status", "online")

        if name and status in {"online", "offline"}:
            db.session.add(Machine(name=name, description=description, status=status))
            db.session.commit()

        return redirect(url_for("admin.machine_list"))

    machines = Machine.query.order_by(Machine.id.asc()).all()
    return render_template("admin/machines.html", machines=machines, current_user=current_user)


@admin_bp.route("/machines/<int:machine_id>/edit", methods=["GET", "POST"])
@login_required
def edit_machine(machine_id: int):
    machine = db.session.get(Machine, machine_id)
    if machine is None:
        abort(404)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        status = request.form.get("status", "online")
        if name and status in {"online", "offline"}:
            machine.name = name
            machine.description = description
            machine.status = status
            db.session.commit()
            return redirect(url_for("admin.machine_list"))

    return render_template("admin/edit_machine.html", machine=machine)


@admin_bp.route("/machines/<int:machine_id>/delete", methods=["POST"])
@login_required
def delete_machine(machine_id: int):
    machine = db.session.get(Machine, machine_id)
    if machine is None:
        abort(404)

    db.session.delete(machine)
    db.session.commit()
    return redirect(url_for("admin.machine_list"))


@admin_bp.route("/machines/<int:machine_id>/toggle-status", methods=["POST"])
@login_required
def toggle_machine_status(machine_id: int):
    machine = db.session.get(Machine, machine_id)
    if machine is None:
        abort(404)

    machine.status = "offline" if machine.status == "online" else "online"
    db.session.commit()
    return redirect(url_for("admin.machine_list"))
