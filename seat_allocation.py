# seat_allocation.py
from db_connect import get_db_connection
from datetime import datetime

def allocate_seats(subject_code):
    """
    Idempotent allocation:
      - Finds exam_id for subject_code
      - Deletes existing allocations for that exam_id
      - Fetches all students of the exam's dept
      - Fetches all classrooms for that dept (ordered by classroom_id)
      - Fills benches left-to-right, classroom-by-classroom
    Returns dict: {"allocated": n, "remaining": m}
    Raises ValueError on invalid input (no exam / no classrooms / no students)
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1) find exam
        cursor.execute("SELECT exam_id, dept_code FROM exam_sessions WHERE subject_code = %s LIMIT 1", (subject_code,))
        exam = cursor.fetchone()
        if not exam:
            raise ValueError(f"No exam found for subject_code '{subject_code}'")

        exam_id = exam['exam_id']
        dept = exam['dept_code']

        # 1b) mark status = allocating
        cursor.execute("UPDATE exam_sessions SET status = %s WHERE exam_id = %s", ('allocating', exam_id))
        conn.commit()

        # 2) delete any existing allocations for this exam (idempotent)
        cursor.execute("DELETE FROM allocations WHERE exam_id = %s", (exam_id,))
        conn.commit()

        # 3) get students for that dept (deterministic order)
        cursor.execute("SELECT usn FROM student_details WHERE dept_code = %s ORDER BY usn", (dept,))
        students = [r['usn'] for r in cursor.fetchall()]
        if not students:
            # revert status
            cursor.execute("UPDATE exam_sessions SET status = %s WHERE exam_id = %s", ('pending', exam_id))
            conn.commit()
            raise ValueError(f"No students found for department '{dept}'")

        # 4) get classrooms for that dept (ordered)
        cursor.execute("""
            SELECT classroom_id, no_of_benches, bench_capacity
            FROM classroom_details
            WHERE dept_code = %s
            ORDER BY classroom_id
        """, (dept,))
        classrooms = cursor.fetchall()
        if not classrooms:
            # revert status
            cursor.execute("UPDATE exam_sessions SET status = %s WHERE exam_id = %s", ('pending', exam_id))
            conn.commit()
            raise ValueError(f"No classrooms found for department '{dept}'")

        # 5) assign students across classrooms, benches and seats
        total_allocated = 0
        student_idx = 0
        total_students = len(students)

        for room in classrooms:
            classroom_id = room['classroom_id']
            no_of_benches = int(room['no_of_benches'])
            bench_capacity = int(room['bench_capacity'])

            for bench_no in range(1, no_of_benches + 1):
                for seat_pos in range(1, bench_capacity + 1):
                    if student_idx >= total_students:
                        break  # no more students
                    usn = students[student_idx]

                    # Insert allocation
                    cursor.execute("""
                        INSERT INTO allocations (exam_id, usn, classroom_id, bench_no, seat_pos, allocated_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (exam_id, usn, classroom_id, bench_no, seat_pos, datetime.now()))

                    student_idx += 1
                    total_allocated += 1

                if student_idx >= total_students:
                    break
            if student_idx >= total_students:
                break

        conn.commit()

        # 6) update exam status
        status = 'done' if total_allocated == total_students else 'failed'
        cursor.execute("UPDATE exam_sessions SET status = %s WHERE exam_id = %s", (status, exam_id))
        conn.commit()

        remaining = total_students - total_allocated
        return {"allocated": total_allocated, "remaining": remaining, "exam_id": exam_id}

    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def deallocate_seats(subject_code):
    """
    Delete allocations for the exam with subject_code.
    Returns number of deleted rows.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT exam_id FROM exam_sessions WHERE subject_code = %s LIMIT 1", (subject_code,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"No exam found for subject_code '{subject_code}'")
        exam_id = row[0] if isinstance(row, tuple) else row['exam_id']

        # delete allocations
        cursor.execute("SELECT COUNT(*) FROM allocations WHERE exam_id = %s", (exam_id,))
        count_before = cursor.fetchone()[0]

        cursor.execute("DELETE FROM allocations WHERE exam_id = %s", (exam_id,))
        conn.commit()

        # set exam status back to pending
        cursor.execute("UPDATE exam_sessions SET status = %s WHERE exam_id = %s", ('pending', exam_id))
        conn.commit()

        return {"deleted": count_before, "exam_id": exam_id}
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()