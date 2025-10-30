from flask import Flask, render_template, request, redirect, url_for, session, flash
from db_connect import get_db_connection
import os
import csv
from seat_allocation import allocate_seats, deallocate_seats
from flask import jsonify
from routes.admin_routes import admin_bp
app = Flask(__name__)
app.secret_key = "supersecretkey"  # Change in production
app.register_blueprint(admin_bp)


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
# ROUTE 5 — Upload Students (CSV)
# --------------------------
@app.route('/admin/upload_students', methods=['POST'])
def upload_students():
    file = request.files.get('file')
    if not file or not file.filename.endswith('.csv'):
        flash("Please upload a valid CSV file.", "danger")
        return redirect(url_for('admin.admin_dashboard'))

    import csv, io
    stream = io.StringIO(file.stream.read().decode("utf-8"))
    reader = csv.DictReader(stream)

    conn = get_db_connection()
    cursor = conn.cursor()
    added, failed = 0, 0

    for row in reader:
        try:
            cursor.execute(
                "INSERT INTO student_details (usn, name, dept_code) VALUES (%s, %s, %s)",
                (
                    row['usn'].strip().upper(),
                    row['name'].strip(),
                    row['dept_code'].strip().upper(),
                ),
            )
            added += 1
        except Exception:
            conn.rollback()
            failed += 1
        else:
            conn.commit()

    conn.close()
    flash(f"Uploaded {added} students (failed: {failed}).", "info")
    return redirect(url_for('admin.admin_dashboard'))


# --------------------------
# ROUTE 6 — Trigger Allocation
# --------------------------
@app.route('/admin/allocate', methods=['POST'])
def allocate_seats_route():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    subject_code = request.form['subject_code']
    allocate_seats(subject_code)
    flash(f"✅ Seat allocation done for {subject_code}", "success")
    return redirect(url_for('admin_dashboard'))

# --------------------------
# ROUTE 7 — Deallocate Seats
# --------------------------
@app.route('/admin/deallocate', methods=['POST'])
def deallocate_seats_route():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    subject_code = request.form['subject_code']
    deallocate_seats(subject_code)
    flash(f"🧹 Deallocated all seats for {subject_code}", "warning")
    return redirect(url_for('admin_dashboard'))

# --------------------------
# ROUTE 8 — UI for Viewing Allocations
# --------------------------
@app.route('/admin/classroom/<classroom_name>')
def view_classroom(classroom_name):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get bench count and classroom id
    cursor.execute("SELECT classroom_id, no_of_benches FROM classroom_details WHERE classroom_name = %s", (classroom_name,))
    classroom = cursor.fetchone()

    if not classroom:
        flash("Classroom not found", "danger")
        return redirect(url_for('admin_dashboard'))

    classroom_id = classroom['classroom_id']
    total_benches = classroom['no_of_benches']

    # Get allocated benches (students)
    cursor.execute("""
        SELECT s.name, s.usn, a.bench_no
        FROM allocations a
        JOIN student_details s ON a.usn = s.usn
        WHERE a.classroom_id = %s
    """, (classroom_id,))
    allocated = cursor.fetchall()
    conn.close()

    allocated_benches = {a['bench_no']: a for a in allocated}

    return render_template('classroom_view.html',
                           classroom_name=classroom_name,
                           total_benches=total_benches,
                           allocated_benches=allocated_benches)

# --------------------------
# Run the Flask app
# --------------------------
if __name__ == "__main__":
    app.run(debug=True)