from flask import Blueprint

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    return {'message': 'Login page'}, 200


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    return {'message': 'Logged out'}, 200
