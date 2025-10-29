from db_connect import get_db_connection

def allocate_seats(subject_code):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Step 1: Get exam details
    cursor.execute("SELECT * FROM exam_sessions WHERE subject_code = %s", (subject_code,))
    exam = cursor.fetchone()
    if not exam:
        print("❌ No exam found for subject:", subject_code)
        return

    dept_code = exam["dept_code"]
    exam_id = exam["exam_id"]

    # Step 2: Get all students of that department
    cursor.execute("SELECT * FROM student_details WHERE dept_code = %s", (dept_code,))
    students = cursor.fetchall()

    # Step 3: Get available classrooms for that department
    cursor.execute("SELECT * FROM classroom_details WHERE dept_code = %s", (dept_code,))
    classrooms = cursor.fetchall()

    if not classrooms or not students:
        print("⚠️ No classrooms or students found for this department.")
        return

    seat_index = 0
    allocations = []

    for room in classrooms:
        total_seats = room["no_of_benches"] * room["bench_capacity"]

        for i in range(room["no_of_benches"]):
            for j in range(room["bench_capacity"]):
                if seat_index >= len(students):
                    break
                student = students[seat_index]
                allocations.append((
                    exam_id, student["usn"], room["classroom_id"], i + 1, j + 1
                ))
                seat_index += 1

            if seat_index >= len(students):
                break
        if seat_index >= len(students):
            break

    # Step 4: Insert into allocations table
    cursor.executemany("""
        INSERT INTO allocations (exam_id, usn, classroom_id, bench_no, seat_pos)
        VALUES (%s, %s, %s, %s, %s)
    """, allocations)

    conn.commit()
    print(f"✅ Allocated {len(allocations)} students for {subject_code}")
    conn.close()


# ---- Run Allocation ----
if __name__ == "__main__":
    allocate_seats("CS101")  # change subject code as needed