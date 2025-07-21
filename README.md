# KPI Manager Flask App

## Setup Instructions
1. Clone the repo
2. Create a virtual environment and install requirements:
pip install -r requirements.txt
3. Create `.env` with your `SECRET_KEY` and `DATABASE_URL`
4. Initialize database:
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
5. Run the app:
flask run