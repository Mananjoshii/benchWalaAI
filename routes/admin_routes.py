from flask import Blueprint, render_template, request, redirect, url_for, flash
import csv, io
from datetime import datetime
from db_connect import get_db_connection
from seat_allocation import allocate_seats, deallocate_seats

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin')
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM student_details")
    students = cursor.fetchall()

    cursor.execute("SELECT * FROM classroom_details")
    classrooms = cursor.fetchall()

    cursor.execute("SELECT * FROM exam_sessions ORDER BY created_at DESC")
    exams = cursor.fetchall()

    conn.close()

    return render_template(
        'admin_dashboard.html',
        students=students,
        classrooms=classrooms,
        exams=exams,
    )


# ------------------ ADD / UPLOAD STUDENT ------------------
@admin_bp.route('/admin/add_student', methods=['POST'])
def add_student():
    usn = request.form['usn'].strip().upper()
    name = request.form['name'].strip()
    dept_code = request.form['dept_code'].strip().upper()

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO student_details (usn, name, dept_code) VALUES (%s, %s, %s)",
            (usn, name, dept_code)
        )
        conn.commit()
        flash("Student added successfully.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {e}", "danger")
    conn.close()
    return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/admin/delete_student/<usn>')
def delete_student(usn):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM student_details WHERE usn = %s", (usn,))
    conn.commit()
    conn.close()
    flash(f"Deleted student {usn}.", "warning")
    return redirect(url_for('admin.admin_dashboard'))


# ------------------ CLASSROOM MANAGEMENT ------------------
@admin_bp.route('/admin/add_classroom', methods=['POST'])
def add_classroom():
    name = request.form['classroom_name'].strip()
    dept_code = request.form['dept_code'].strip().upper()
    benches = int(request.form['no_of_benches'])
    capacity = int(request.form['bench_capacity'])
    location = request.form.get('location', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO classroom_details (classroom_name, dept_code, no_of_benches, bench_capacity, location)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, dept_code, benches, capacity, location))
        conn.commit()
        flash("Classroom added successfully.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {e}", "danger")
    conn.close()
    return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/admin/delete_classroom/<int:id>')
def delete_classroom(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM classroom_details WHERE classroom_id = %s", (id,))
    conn.commit()
    conn.close()
    flash(f"Deleted classroom ID {id}.", "warning")
    return redirect(url_for('admin.admin_dashboard'))


# ------------------ EXAM SESSION MANAGEMENT ------------------
@admin_bp.route('/admin/add_exam_session', methods=['POST'])
def add_exam_session():
    subject_code = request.form['subject_code'].strip().upper()
    start_time = request.form['start_time']
    end_time = request.form['end_time']
    dept_code = request.form['dept_code'].strip().upper()

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO exam_sessions (subject_code, start_time, end_time, dept_code)
            VALUES (%s, %s, %s, %s)
        """, (subject_code, start_time, end_time, dept_code))
        conn.commit()
        flash("Exam session added.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {e}", "danger")
    conn.close()
    return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/admin/delete_exam/<int:id>')
def delete_exam_session(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM exam_sessions WHERE exam_id = %s", (id,))
    conn.commit()
    conn.close()
    flash(f"Deleted exam session {id}.", "warning")
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/allocate_seats', methods=['POST'])
def allocate_seats_route():
    subject_code = request.form['subject_code']
    allocate_seats(subject_code)
    flash(f"Seats allocated for {subject_code}", "success")
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/deallocate_seats', methods=['POST'])
def deallocate_seats_route():
    subject_code = request.form['subject_code']
    deallocate_seats(subject_code)
    flash(f"Deallocated seats for {subject_code}", "info")
    return redirect(url_for('admin.admin_dashboard'))