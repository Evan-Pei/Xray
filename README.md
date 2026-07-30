# Xray

A Python-based tool booking and calendaring webpage for managing appointments and scheduling.

## Features

- **Dashboard** (`/dashboard`) — summary metrics for active machines, scheduled bookings, and pending requests
- **狀態視窗 – Machine Status Panel** — live-style status view on the dashboard showing each machine as *online*, *maintenance*, or *offline*
- **行事曆 – Schedule Calendar** (`/calendar`) — monthly calendar grid displaying all booked time-slots for X-ray resources
- **Admin Backend** (`/auth/login` -> `/admin/machines`) — authenticated machine record management with list/create/edit/delete/status toggle
- Web-based interface with server-rendered HTML/CSS (no heavy frontend frameworks)

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+** — [Download Python](https://www.python.org/downloads/)
- **pip** — Python package manager (usually comes with Python)
- **Git** — [Download Git](https://git-scm.com/downloads)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Evan-Pei/Xray.git
cd Xray
```

### 2. Create a Virtual Environment (Recommended)

```bash
# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Running the Application

### Start the Development Server

```bash
python app.py
```

Or with the Flask CLI:

```bash
flask run
```

The application is accessible at `http://localhost:5000`.

## Usage

1. Open your web browser and navigate to `http://localhost:5000`
2. From the **Home** page, click **Dashboard** or **行事曆 Calendar**
3. The **Dashboard** shows summary metrics and the **狀態視窗** (machine status panel) with real-time-style status badges
4. The **行事曆 Calendar** page (`/calendar`) shows a monthly grid with all scheduled bookings
5. The **Admin Backend** allows editable machine management after login (`ADMIN_USERNAME` / `ADMIN_PASSWORD`; in testing only, default credentials are `admin` / `admin123`)

## Configuration

- Modify configuration settings in `config.py` or environment variables as needed
- Database credentials and API keys should be stored in a `.env` file (do not commit this file)
- For admin login, set `ADMIN_USERNAME` and `ADMIN_PASSWORD` in your environment (`ADMIN_PASSWORD` is required outside tests)

## Development

### Running Tests

```bash
pytest
```

### Code Style

Follow PEP 8 guidelines for Python code.

## Troubleshooting

- **Port already in use**: Change the port in the configuration or kill the process using that port
- **Module not found errors**: Ensure your virtual environment is activated and dependencies are installed
- **Database connection issues**: Verify database configuration in `.env` or `config.py`
- **After model changes (SQLite)**: this project uses `db.create_all()` and does not run schema migrations for existing SQLite files. If you see missing-column errors, delete `xray.db` and restart the app to rebuild tables.

## Contributing

1. Create a new branch for your feature
2. Commit your changes
3. Push to your branch
4. Submit a pull request

## License

See LICENSE file for details.

## Support

For issues or questions, please open a GitHub issue.
