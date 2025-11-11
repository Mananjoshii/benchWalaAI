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
# ROUTE 4 — Student Login (UPDATED FOR 2-D CLASSROOM)
# --------------------------
@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        usn = request.form['usn'].strip().upper()
        subject_code = request.form['subject_code'].strip().upper()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # ---- 1. Get the student's own seat -----------------
        query = """
        SELECT s.name, s.usn, e.subject_code, e.start_time, e.end_time,
               c.classroom_id, c.classroom_name, a.seat_pos, a.bench_no,
               c.location, c.no_of_benches
        FROM allocations a
        JOIN student_details s   ON a.usn = s.usn
        JOIN exam_sessions e     ON a.exam_id = e.exam_id
        JOIN classroom_details c ON a.classroom_id = c.classroom_id
        WHERE s.usn = %s AND e.subject_code = %s
        """
        cursor.execute(query, (usn, subject_code))
        result = cursor.fetchone()

        if not result:
            conn.close()
            flash("No allocation found for this USN and subject.", "warning")
            return render_template('student_login.html')

        # ---- 2. Get **all** seats in the same classroom -----
        classroom_id = result['classroom_id']
        cursor.execute("""
            SELECT a.bench_no, a.seat_pos, s.name AS student_name, s.usn AS student_usn
            FROM allocations a
            JOIN student_details s ON a.usn = s.usn
            WHERE a.classroom_id = %s
        """, (classroom_id,))
        alloc_rows = cursor.fetchall()
        conn.close()

        # ---- 3. Build the structures the 2-D UI expects -----
        allocated_seats = {}          # {bench_no: {"L": true, "R": true}}
        student_details = {}          # {"5R": {"name": "...", "usn": "..."}}

        for row in alloc_rows:
            bench = row['bench_no']
            side  = row['seat_pos']          # 'L' or 'R'
            if bench not in allocated_seats:
                allocated_seats[bench] = {}
            allocated_seats[bench][side] = True

            key = f"{bench}{side}"
            student_details[key] = {
                "name": row['student_name'],
                "usn" : row['student_usn']
            }

        # ---- 4. Fallback for total benches ------------------
        total_benches = result.get('no_of_benches') or 20

        # ---- 5. Render the 2-D page -------------------------
        return render_template(
            "student_result.html",
            data=result,
            total_benches=total_benches,
            allocated_seats=allocated_seats,   # nested dict
            student_details=student_details    # for hover tooltips
        )

    return render_template('student_login.html')

# --------------------------
# ROUTE — Upload Students (CSV)
# --------------------------
@app.route('/admin/upload_students', methods=['POST'])
def upload_students():
    file = request.files.get('file')

    if not file or not file.filename.endswith('.csv'):
        flash("Please upload a valid CSV file (.csv).", "danger")
        return redirect(url_for('admin.admin_dashboard'))

    import csv, io
    stream = io.StringIO(file.stream.read().decode("utf-8"))
    reader = csv.DictReader(stream)

    required_cols = {'usn', 'name', 'dept_code'}
    if not required_cols.issubset(reader.fieldnames):
        flash(f"CSV missing required columns: {required_cols}", "danger")
        return redirect(url_for('admin.admin_dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()
    added, failed = 0, 0

    for row in reader:
        try:
            cursor.execute(
                """
                INSERT INTO student_details (usn, name, dept_code)
                VALUES (%s, %s, %s)
                """,
                (
                    row['usn'].strip().upper(),
                    row['name'].strip(),
                    row['dept_code'].strip().upper(),
                ),
            )
            added += 1
        except Exception as e:
            print("❌ Error inserting:", row, e)
            failed += 1
            conn.rollback()
        else:
            conn.commit()

    conn.close()
    flash(f"✅ Uploaded {added} students (failed: {failed}).", "info")
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
# ROUTE — Upload Classrooms (CSV)
# --------------------------
@app.route('/admin/upload_classrooms', methods=['POST'])
def upload_classrooms():
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
            cursor.execute("""
                INSERT INTO classroom_details 
                (classroom_name, dept_code, no_of_benches, bench_capacity, location)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                row['classroom_name'].strip(),
                row['dept_code'].strip().upper(),
                int(row['no_of_benches']),
                int(row['bench_capacity']),
                row.get('location', '').strip()
            ))
            conn.commit()
            added += 1
        except Exception as e:
            conn.rollback()
            failed += 1
            print("Classroom insert failed:", e)

    conn.close()
    flash(f"Uploaded {added} classrooms (failed: {failed}).", "info")
    return redirect(url_for('admin.admin_dashboard'))


# --------------------------
# ROUTE — Upload Exam Sessions (CSV)
# --------------------------
@app.route('/admin/upload_exams', methods=['POST'])
def upload_exams():
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
            cursor.execute("""
                INSERT INTO exam_sessions
                (subject_code, start_time, end_time, dept_code)
                VALUES (%s, %s, %s, %s)
            """, (
                row['subject_code'].strip().upper(),
                row['start_time'].strip(),  # format: YYYY-MM-DD HH:MM:SS
                row['end_time'].strip(),
                row['dept_code'].strip().upper()
            ))
            conn.commit()
            added += 1
        except Exception as e:
            conn.rollback()
            failed += 1
            print("Exam insert failed:", e)

    conn.close()
    flash(f"Uploaded {added} exam sessions (failed: {failed}).", "info")
    return redirect(url_for('admin.admin_dashboard'))

# --------------------------
# Run the Flask app
# --------------------------
if __name__ == "__main__":
    app.run(debug=True)