# 💰 Expense Tracker

A Flask-based web application to track your daily expenses, manage budgets, set financial goals, and export reports.

---

## ✨ Features

- 🔐 User Authentication (Login / Signup)
- 📊 Dashboard with spending overview
- 💸 Add, Edit, Delete Transactions
- 📁 Category-wise Budget Management
- 🎯 Financial Goals Tracking
- 📤 Export data as **CSV** or **PDF**
- 👤 User Profile Management

---

## 🛠️ Tech Stack

- **Backend:** Python 3.14, Flask 3.x
- **Database:** MySQL
- **Frontend:** HTML, CSS (Jinja2 templates)
- **PDF Export:** ReportLab
- **Package Manager:** [uv](https://github.com/astral-sh/uv)

---

## ⚙️ Setup & Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd expense_tracker
```

### 2. Create virtual environment & install dependencies

```bash
uv sync
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your MySQL credentials:

```env
SECRET_KEY=your_random_secret_key
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=expense_tracker
```

### 4. Create MySQL database

```sql
CREATE DATABASE expense_tracker;
```

### 5. Run the application

```bash
python app.py
```

App will be available at: **http://localhost:5000**

---

## 📡 API Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Home / Index page |
| `/login` | GET, POST | User login |
| `/signup` | GET, POST | User registration |
| `/dashboard` | GET | Main dashboard |
| `/logout` | GET | Logout user |
| `/profile` | GET | View profile |
| `/api/profile` | POST | Update profile |
| `/api/transactions` | GET | List all transactions |
| `/api/transactions` | POST | Add new transaction |
| `/api/transactions/<id>` | PUT | Edit a transaction |
| `/api/transactions/<id>` | DELETE | Delete a transaction |
| `/api/budgets` | GET | List all budgets |
| `/api/budgets` | POST | Add/update a budget |
| `/api/budgets/<category>` | DELETE | Delete a budget |
| `/api/goals` | GET | List all goals |
| `/api/goals` | POST | Add a new goal |
| `/api/goals/<id>` | PUT | Update a goal |
| `/api/goals/<id>` | DELETE | Delete a goal |
| `/export/csv` | GET | Export transactions as CSV |
| `/export/pdf` | GET | Export transactions as PDF |

---

## 📂 Project Structure

```
expense_tracker/
├── app.py                  # Main Flask application
├── config.py               # Database & app configuration
├── .env.example            # Environment variables template
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Project metadata (uv)
├── templates/              # HTML templates (Jinja2)
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── profile.html
│   ├── add_expense.html
│   └── edit_expense.html
├── static/
│   └── style.css           # Application styles
└── src/
    └── expense_tracker/
        └── __init__.py
```

---

## 🚀 Development

Run with debug mode:

```bash
python app.py
```

Run tests:

```bash
pytest
```

---

## 📄 License

MIT License — free to use and modify.
