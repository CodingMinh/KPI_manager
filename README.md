# KPI Manager Flask App

This is a simple KPI management app built with Flask. I built it during my 3-month internship at VNPT and therefore this project is still a __work in progress__. So far I was able to complete the backend logic of creating, editing, and deleting departments, projects, tasks, and users to allow for tracking tasks across projects across departments, assigning tasks to some users and having their KPI scored by managers.

## Setup Instructions
1. Clone the repo
2. Create a virtual environment and install requirements:
pip install -r requirements.txt
3. Create `.env` with:
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///your_database_here
MAIL_SERVER=localhost
MAIL_PORT=8025
MAIL_USE_TLS=False
MAIL_USE_SSL=False
MAIL_USERNAME=None
MAIL_PASSWORD=None
4. Create `.flaskenv` with:
FLASK_APP=run.py
FLASK_DEBUG=1
5. Start local SMTP server (for testing emails):
python -m aiosmtpd -n -l localhost:8025 (start on a 2nd terminal)
6. Initialize database:
- flask db init
- flask db migrate -m "Initial migration"
- flask db upgrade
7. Run the app:
flask run
8. Access the app by typing localhost:5000 or http://127.0.0.1:5000 in your browser