from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from models import Machine, db

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/", methods=["GET"])
@login_required
def index():
    return redirect(url_for("admin.machine_list"))


@admin_bp.route("/machines", methods=["GET", "POST"])
@login_required
def machine_list():
    """List all machines and handle creation"""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if name:
            try:
                db.session.add(Machine(name=name, description=description))
                db.session.commit()
                flash("Machine created successfully.")
            except IntegrityError:
                db.session.rollback()
                flash("A machine with this name already exists.", "error")
        else:
            flash("Please provide a machine name.", "error")

        return redirect(url_for("admin.machine_list"))

    machines = Machine.query.order_by(Machine.id.asc()).all()
    return render_template(
        "admin/machines.html",
        machines=machines,
        current_user=current_user,
    )


@admin_bp.route("/machines/<int:machine_id>/edit", methods=["GET", "POST"])
@login_required
def edit_machine(machine_id: int):
    """Edit a specific machine"""
    machine = db.session.get(Machine, machine_id)
    if machine is None:
        abort(404)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Please provide a machine name.", "error")
        else:
            machine.name = name
            machine.description = description
            try:
                db.session.commit()
                flash("Machine updated successfully.")
                return redirect(url_for("admin.machine_list"))
            except IntegrityError:
                db.session.rollback()
                flash("A machine with this name already exists.", "error")

    return render_template("admin/edit_machine.html", machine=machine)


@admin_bp.route("/machines/<int:machine_id>/delete", methods=["POST"])
@login_required
def delete_machine(machine_id: int):
    """Delete a machine"""
    machine = db.session.get(Machine, machine_id)
    if machine is None:
        abort(404)

    db.session.delete(machine)
    db.session.commit()
    flash("Machine deleted.")
    return redirect(url_for("admin.machine_list"))
