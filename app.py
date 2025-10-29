from flask import Flask, render_template, request, redirect, url_for, session, flash
from db_connect import get_db_connection
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Change in production


# --------------------------
# ROUTE 1 — Landing Page
# --------------------------
@app.route('/')
def home():
    return render_template('index.html')


# --------------------------
# ROUTE 2 — Admin Login
# --------------------------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # For now, simple hardcoded check
        if username == "admin" and password == "rvce123":
            session['admin'] = username
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid credentials", "danger")

    return render_template('admin_login.html')


# --------------------------
# ROUTE 3 — Admin Dashboard
# --------------------------
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html')


# --------------------------
# ROUTE 4 — Student Login
# --------------------------
@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        usn = request.form['usn']
        subject_code = request.form['subject_code']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT s.name, s.usn, e.subject_code, e.start_time, e.end_time, c.classroom_name
        FROM allocations a
        JOIN student_details s ON a.usn = s.usn
        JOIN exam_sessions e ON a.exam_id = e.exam_id
        JOIN classroom_details c ON a.classroom_id = c.classroom_id
        WHERE s.usn = %s AND e.subject_code = %s
        """
        cursor.execute(query, (usn, subject_code))
        result = cursor.fetchone()
        conn.close()

        if result:
            return render_template('student_result.html', data=result)
        else:
            flash("No allocation found for this USN and subject.", "warning")

    return render_template('student_login.html')


# --------------------------
# Run the Flask app
# --------------------------
if __name__ == "__main__":
    app.run(debug=True)