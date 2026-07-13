import calendar
from datetime import date

from flask import Blueprint, render_template

web_bp = Blueprint('web', __name__, url_prefix='/')

# ---------------------------------------------------------------------------
# Mock data – replace with real DB queries when a booking model is available
# ---------------------------------------------------------------------------

_MACHINES = [
    {"name": "X-Ray 1",    "description": "High-resolution X-ray machine",  "status": "online"},
    {"name": "X-Ray 2",    "description": "Fast throughput X-ray machine",   "status": "maintenance"},
    {"name": "CT Scanner", "description": "Computed tomography scanner",      "status": "online"},
]

_BOOKINGS = [
    {"day": 14, "time": "09:00", "machine": "X-Ray 1",    "patient": "Patient A"},
    {"day": 14, "time": "11:30", "machine": "CT Scanner", "patient": "Patient B"},
    {"day": 15, "time": "08:30", "machine": "X-Ray 1",    "patient": "Patient C"},
    {"day": 16, "time": "14:00", "machine": "X-Ray 2",    "patient": "Patient D"},
    {"day": 17, "time": "10:00", "machine": "CT Scanner", "patient": "Patient E"},
    {"day": 21, "time": "09:30", "machine": "X-Ray 1",    "patient": "Patient F"},
    {"day": 22, "time": "13:00", "machine": "X-Ray 2",    "patient": "Patient G"},
]


@web_bp.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@web_bp.route('/dashboard', methods=['GET'])
def dashboard():
    online_count = sum(1 for m in _MACHINES if m['status'] == 'online')
    metrics = [
        {"label": "Active Machines",   "value": online_count},
        {"label": "Scheduled Today",   "value": 12},
        {"label": "Pending Requests",  "value": 4},
    ]
    return render_template('dashboard.html', metrics=metrics, machines=_MACHINES)


@web_bp.route('/calendar', methods=['GET'])
def calendar_view():
    today = date.today()
    year, month = today.year, today.month

    # Build a list-of-weeks; each week is a list of day numbers (0 = padding)
    cal = calendar.monthcalendar(year, month)
    month_name = today.strftime('%B %Y')

    # Map day -> list of bookings for quick lookup in the template
    bookings_by_day: dict[int, list[dict]] = {}
    for b in _BOOKINGS:
        bookings_by_day.setdefault(b['day'], []).append(b)

    return render_template(
        'calendar.html',
        cal=cal,
        month_name=month_name,
        today_day=today.day,
        bookings_by_day=bookings_by_day,
    )
