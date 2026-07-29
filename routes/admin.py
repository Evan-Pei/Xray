from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from models import Machine, MACHINE_STATUS_ONLINE, MACHINE_STATUS_OFFLINE, MACHINE_STATUS_MAINTENANCE, MACHINE_VALID_STATUSES, db

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
        machine_id = request.form.get("id", "").strip()
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not machine_id or not name:
            flash("Please provide both ID and name.", "error")
        else:
            try:
                machine_id_int = int(machine_id)
                db.session.add(Machine(id=machine_id_int, name=name, description=description))
                db.session.commit()
                flash("Machine created successfully.")
            except ValueError:
                flash("ID must be a number.", "error")
            except IntegrityError:
                db.session.rollback()
                flash("A machine with this ID or name already exists.", "error")

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
        new_id = request.form.get("id", "").strip()
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        status = request.form.get("status", "").strip()

        if not new_id or not name:
            flash("Please provide both ID and name.", "error")
        elif status not in MACHINE_VALID_STATUSES:
            flash("Invalid status selected.", "error")
        else:
            try:
                new_id_int = int(new_id)
                
                # If ID changed, delete old and create new
                if new_id_int != machine_id:
                    # Check if new ID already exists
                    if db.session.get(Machine, new_id_int):
                        flash("A machine with this ID already exists.", "error")
                        return render_template(
                            "admin/edit_machine.html",
                            machine=machine,
                            statuses=sorted(MACHINE_VALID_STATUSES),
                        )
                    
                    # Delete old and create new
                    db.session.delete(machine)
                    db.session.flush()
                    new_machine = Machine(id=new_id_int, name=name, description=description, status=status)
                    db.session.add(new_machine)
                else:
                    # Just update existing
                    machine.name = name
                    machine.description = description
                    machine.status = status
                
                db.session.commit()
                flash("Machine updated successfully.")
                return redirect(url_for("admin.machine_list"))
            except ValueError:
                flash("ID must be a number.", "error")
            except IntegrityError:
                db.session.rollback()
                flash("A machine with this name already exists.", "error")

    return render_template(
        "admin/edit_machine.html",
        machine=machine,
        statuses=sorted(MACHINE_VALID_STATUSES),
    )


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
