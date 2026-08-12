from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def _post_login_redirect():
    if current_user.is_admin():
        return redirect(url_for('admin.machine_list'))
    return redirect(url_for('web.calendar_view'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if current_user.is_authenticated:
        return _post_login_redirect()

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return _post_login_redirect()
        error = 'Invalid username or password'

    return render_template('auth/login.html', error=error), 200


@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """Logout user"""
    logout_user()
    return redirect(url_for('auth.login'))
