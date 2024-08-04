from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from cs50 import SQL
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQL("sqlite:///finance_tracker.db")

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    user = db.execute("SELECT * FROM User WHERE id = ?", user_id)
    if user:
        user = user[0]
        return User(user["id"], user["username"], user["password"])
    return None

@app.route('/')
def index():
    return render_template('index.html')

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirmation = request.form['confirm-password']
        if (password == confirmation):
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            db.execute("INSERT INTO User (username, password) VALUES (?, ?)", username, hashed_password)
            user = db.execute("SELECT * FROM User WHERE username = ?", username)
            if user:
                user = user[0]
                login_user(User(user["id"], user["username"], user["password"]))
                return redirect(url_for('dashboard'))
        else:
            flash("Passwords did not match")
    return render_template('register.html')
# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db.execute("SELECT * FROM User WHERE username = ?", username)
        if user and check_password_hash(user[0]["password"], password):
            user = user[0]
            login_user(User(user["id"], user["username"], user["password"]))
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html')

# Dashboard route
@app.route('/dashboard')
@login_required
def dashboard():
    incomes = db.execute("SELECT * FROM Income WHERE user_id = ?", current_user.id)
    expenses = db.execute("SELECT * FROM Expense WHERE user_id = ?", current_user.id)
    dates = db.execute("""SELECT SUM(amount) AS total_amount, date FROM Income GROUP BY date ORDER BY date""")
    total_income = db.execute("SELECT SUM(amount) AS total FROM Income WHERE user_id = ?", current_user.id)[0]['total']
    total_expense = db.execute("SELECT SUM(amount) AS total FROM Expense WHERE user_id = ?", current_user.id)[0]['total']
    try:
        savings = total_income - total_expense
    except:
        savings = 'Brokie'
    over_time_expenditure = []
    over_time_incomes = []
    dates_label = []
    dates_label1 = []
    i = 0
    for amount, date in dates:
        try:
                # Convert the date to datetime object
            expense_date = datetime.strptime(expenses[i]["date"], "%Y-%m-%d %H:%M:%S").day

                # Check if the expense date's month is not the current month

                # Add to labels and expenditures
            dates_label.append(expense_date)
            over_time_expenditure.append(expenses[i]["amount"])
            income_date = datetime.strptime(incomes[i]["date"], "%Y-%m-%d %H:%M:%S").day

                # Check if the expense date's month is not the current month

                # Add to labels and expenditures
            dates_label1.append(income_date)
            over_time_incomes.append(incomes[i]["amount"])
            i=i+1
        except:
            print(".")


    return render_template('dashboard.html', incomes=incomes, expenses=expenses,  over_time_expenditure=json.dumps(over_time_expenditure), dates_label =json.dumps(dates_label), over_time_incomes=json.dumps(over_time_incomes), dates_label1 =json.dumps(dates_label1), Total_income = total_income, Total_expense = total_expense, savings = savings)


@app.route('/deletei/<int:id>', methods=['POST'])
@login_required
def deletei(id):
    db.execute("DELETE FROM Income WHERE id = ? AND user_id = ?", id, current_user.id)
    return redirect(url_for('dashboard'))
@app.route('/deletee/<int:id>', methods=['POST'])
@login_required
def deletee(id):
    db.execute("DELETE FROM Expense WHERE id = ? AND user_id = ?", id, current_user.id)
    return redirect(url_for('dashboard'))
# Add income route
@app.route('/add_income', methods=['POST'])
@login_required
def add_income():
    amount = request.form['amount']
    description = request.form['description']
    db.execute("INSERT INTO Income (amount, description, user_id, type) VALUES (?, ?, ?, ?)", amount, description, current_user.id, "Credit")
    return redirect(url_for('dashboard'))

# Add expense route
@app.route('/add_expense', methods=['POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        amount = request.form['amount']
        description = request.form['description']
        db.execute("INSERT INTO Expense (amount, description, user_id, type) VALUES (?, ?, ?, ?)", amount, description, current_user.id, "Debit")
        return redirect(url_for('dashboard'))
    else:
        income = db.execute("")
        expense = db.execute("")


# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Reset expenses (to be run as a scheduled task)
@app.cli.command('reset_expenses')
def reset_expenses():
    current_month = datetime.utcnow().month
    expenses = db.execute("SELECT * FROM Expense")
    for expense in expenses:
        if datetime.strptime(expense["date"], "%Y-%m-%d %H:%M:%S").month != current_month:
            db.execute("DELETE FROM Expense WHERE id = ?", expense["id"])
    print("Expenses have been reset")


    app.run(debug=True)
