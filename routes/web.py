from flask import Blueprint, render_template

web_bp = Blueprint('web', __name__, url_prefix='/')


@web_bp.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@web_bp.route('/dashboard', methods=['GET'])
def dashboard():
    metrics = [
        {"label": "Active Machines", "value": 3},
        {"label": "Scheduled Today", "value": 12},
        {"label": "Pending Requests", "value": 4},
    ]
    return render_template('dashboard.html', metrics=metrics)
