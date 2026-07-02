from flask import Blueprint

web_bp = Blueprint('web', __name__, url_prefix='/')


@web_bp.route('/', methods=['GET'])
def index():
    return {'message': 'Welcome to Xray'}, 200


@web_bp.route('/dashboard', methods=['GET'])
def dashboard():
    return {'message': 'Dashboard'}, 200
