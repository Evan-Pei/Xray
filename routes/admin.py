from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from models import (
    MACHINE_STATUS_MAINTENANCE,
    MACHINE_STATUS_OFFLINE,
    MACHINE_STATUS_ONLINE,
    MACHINE_VALID_STATUSES,
    Machine,
    db,
)

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
        requested_status = request.form.get("status", "").strip()
        status = requested_status if requested_status in MACHINE_VALID_STATUSES else None

        if name and description and status:
            db.session.add(Machine(name=name, description=description, status=status))
            db.session.commit()
            flash("Machine created successfully.")
        else:
            flash("Please provide valid name, description, and status.", "error")

        return redirect(url_for("admin.machine_list"))

    machines = Machine.query.order_by(Machine.id.asc()).all()
    return render_template(
        "admin/machines.html",
        machines=machines,
        current_user=current_user,
        statuses=sorted(MACHINE_VALID_STATUSES),
    )


@admin_bp.route("/machines/<int:machine_id>/edit", methods=["GET", "POST"])
@login_required
def edit_machine(machine_id: int):
    machine = db.session.get(Machine, machine_id)
    if machine is None:
        abort(404)

    if request.method == "POST":
        requested_id = request.form.get("id", "").strip()
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        requested_status = request.form.get("status", "").strip()
        status = requested_status if requested_status in MACHINE_VALID_STATUSES else None

        try:
            new_machine_id = int(requested_id)
        except ValueError:
            new_machine_id = None

        if new_machine_id is not None and new_machine_id <= 0:
            new_machine_id = None

        if not (name and description and status):
            flash("Please provide valid name, description, and status.", "error")
        elif new_machine_id is None:
            flash("Please provide a valid machine ID.", "error")
        else:
            if new_machine_id != machine.id and db.session.get(Machine, new_machine_id) is not None:
                flash("Machine ID is already in use.", "error")
                return render_template(
                    "admin/edit_machine.html",
                    machine=machine,
                    statuses=sorted(MACHINE_VALID_STATUSES),
                )

            machine.id = new_machine_id
            machine.name = name
            machine.description = description
            machine.status = status
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                db.session.refresh(machine)
                flash("Machine ID is already in use.", "error")
                return render_template(
                    "admin/edit_machine.html",
                    machine=machine,
                    statuses=sorted(MACHINE_VALID_STATUSES),
                )

            flash("Machine updated successfully.")
            return redirect(url_for("admin.machine_list"))

    return render_template(
        "admin/edit_machine.html",
        machine=machine,
        statuses=sorted(MACHINE_VALID_STATUSES),
    )


@admin_bp.route("/machines/<int:machine_id>/delete", methods=["POST"])
@login_required
def delete_machine(machine_id: int):
    machine = db.session.get(Machine, machine_id)
    if machine is None:
        abort(404)

    db.session.delete(machine)
    db.session.commit()
    flash("Machine deleted.")
    return redirect(url_for("admin.machine_list"))


@admin_bp.route("/machines/<int:machine_id>/toggle-status", methods=["POST"])
@login_required
def toggle_machine_status(machine_id: int):
    machine = db.session.get(Machine, machine_id)
    if machine is None:
        abort(404)

    if machine.status == MACHINE_STATUS_ONLINE:
        machine.status = MACHINE_STATUS_OFFLINE
    elif machine.status == MACHINE_STATUS_OFFLINE:
        machine.status = MACHINE_STATUS_ONLINE
    elif machine.status == MACHINE_STATUS_MAINTENANCE:
        machine.status = MACHINE_STATUS_ONLINE
    else:
        machine.status = MACHINE_STATUS_ONLINE

    db.session.commit()
    flash("Machine status updated.")
    return redirect(url_for("admin.machine_list"))