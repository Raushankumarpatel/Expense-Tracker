import sys
import os

# Add project root to path so app.py can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def main() -> None:
    """Entry point to start the Expense Tracker Flask application."""
    from app import app
    app.run(debug=False, host="0.0.0.0", port=5000)
