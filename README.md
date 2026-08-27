# 💰 Expense Tracker

A full-stack personal finance management web application built using Flask and SQLite.

## 🚀 Features

- User Registration and Login
- Secure Password Hashing
- Add Expenses
- View Expenses
- Search Expenses
- Filter Expenses by Month
- Edit Expenses
- Delete Expenses
- Dashboard Statistics
- Recent Transactions
- Category-wise Expense Analytics
- Monthly Expense Trend
- CSV Export
- PDF Export
- Dark Mode
- Responsive Mobile UI

## 🛠️ Technologies Used

### Frontend
- HTML5
- CSS3
- Bootstrap 5
- JavaScript
- Chart.js

### Backend
- Python
- Flask

### Database
- SQLite

### Libraries
- Werkzeug
- FPDF

## 📊 Dashboard

The dashboard provides:

- Total Expense
- Transaction Count
- Category Count
- Highest Expense
- Lowest Expense
- Average Expense
- Current Month Expense
- Monthly Expense Trend
- Category-wise Expense Chart
- Recent Transactions

## 🔐 Authentication

The application includes:

- User registration
- Login and logout
- Password hashing
- Session-based authentication
- User-specific expense data

## 📁 Project Structure

```text
expense-tracker/
│
├── app.py
├── expenses.db
├── requirements.txt
├── README.md
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   ├── add_expense.html
│   ├── view_expense.html
│   ├── edit_expense.html
│   └── reports.html
│
└── static/
    └── style.css
