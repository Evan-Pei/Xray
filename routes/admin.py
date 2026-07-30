from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from models import (
    MACHINE_STATUS_MAINTENANCE,
    MACHINE_STATUS_OFFLINE,
    MACHINE_STATUS_ONLINE,
    MACHINE_VALID_STATUSES,
    Machine,
    User,
    db,
    login_manager,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    """Decorator: require authenticated admin user, else 401-redirect or 403."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        if not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated


def _is_checked(field_name):
    return request.form.get(field_name) in {"on", "true", "1", "yes"}


@admin_bp.route("/", methods=["GET"])
@admin_required
def index():
    return redirect(url_for("admin.machine_list"))


@admin_bp.route("/machines", methods=["GET", "POST"])
@admin_required
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
@admin_required
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
@admin_required
def delete_machine(machine_id: int):
    """Delete a machine"""
    machine = db.session.get(Machine, machine_id)
    if machine is None:
        abort(404)

    db.session.delete(machine)
    db.session.commit()
    flash("Machine deleted.")
    return redirect(url_for("admin.machine_list"))


@admin_bp.route("/users", methods=["GET", "POST"])
@admin_required
def user_list():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        is_qualified = _is_checked("is_qualified")

        if not username or not password:
            flash("Please provide both username and password.", "error")
        else:
            try:
                user = User(username=username, is_qualified=is_qualified)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                flash("User created successfully.")
            except IntegrityError:
                db.session.rollback()
                flash("A user with this username already exists.", "error")
        return redirect(url_for("admin.user_list"))

    users = User.query.order_by(User.id.asc()).all()
    return render_template("admin/users.html", users=users, edit_user=None)


@admin_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_user(user_id: int):
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        is_qualified = _is_checked("is_qualified")

        if not username:
            flash("Username is required.", "error")
        else:
            try:
                user.username = username
                user.is_qualified = is_qualified
                if password:
                    user.set_password(password)
                db.session.commit()
                flash("User updated successfully.")
                return redirect(url_for("admin.user_list"))
            except IntegrityError:
                db.session.rollback()
                flash("A user with this username already exists.", "error")

    users = User.query.order_by(User.id.asc()).all()
    return render_template("admin/users.html", users=users, edit_user=user)


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id: int):
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)
    if user.id == current_user.id:
        flash("You cannot delete your own account.", "error")
        return redirect(url_for("admin.user_list"))

    db.session.delete(user)
    db.session.commit()
    flash("User deleted.")
    return redirect(url_for("admin.user_list"))


@admin_bp.route("/users/<int:user_id>/toggle-qualified", methods=["POST"])
@admin_required
def toggle_user_qualified(user_id: int):
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)
    user.is_qualified = not user.is_qualified
    db.session.commit()
    flash("User qualification updated.")
    return redirect(url_for("admin.user_list"))
