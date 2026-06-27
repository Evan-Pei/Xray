# Xray

A Python-based tool booking and calendaring webpage for managing appointments and scheduling.

## Features

- Tool booking system
- Calendar management
- Appointment scheduling
- Web-based interface

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

Or if using Flask/Django:

```bash
# For Flask
flask run

# For Django
python manage.py runserver
```

The application should be accessible at `http://localhost:5000` or `http://localhost:8000` (depending on your framework).

## Usage

1. Open your web browser and navigate to the local server address
2. Create an account or log in
3. Book tools or schedule appointments using the calendar interface
4. View and manage your bookings

## Configuration

- Modify configuration settings in `config.py` or environment variables as needed
- Database credentials and API keys should be stored in a `.env` file (do not commit this file)

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

## Contributing

1. Create a new branch for your feature
2. Commit your changes
3. Push to your branch
4. Submit a pull request

## License

See LICENSE file for details.

## Support

For issues or questions, please open a GitHub issue.
