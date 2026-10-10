import os

SECRET_KEY = os.environ.get("SECRET_KEY", "expense_tracker_secret_key")

# MySQL connection settings — set via environment variables or .env
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "  ")
DB_NAME = os.environ.get("DB_NAME", "expense_tracker")
