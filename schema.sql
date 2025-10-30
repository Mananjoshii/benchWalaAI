
-- ===============================
--  RVCE Exam Management System Schema
-- ===============================

-- 1. Student Details
CREATE TABLE student_details (
  usn VARCHAR(20) NOT NULL,
  name VARCHAR(200) NOT NULL,
  dept_code VARCHAR(10) NOT NULL,    -- 'CSE', 'CD', 'CY'
  PRIMARY KEY (usn)
);

-- 2. Classroom Details
CREATE TABLE classroom_details (
  classroom_id INT AUTO_INCREMENT PRIMARY KEY,
  classroom_name VARCHAR(50) NOT NULL UNIQUE,
  dept_code VARCHAR(10) NOT NULL,     -- Department that uses this classroom
  no_of_benches INT NOT NULL,
  bench_capacity INT NOT NULL DEFAULT 2,  -- Number of students per bench
  location VARCHAR(200)
);

-- 3. Exam Sessions
CREATE TABLE exam_sessions (
  exam_id INT AUTO_INCREMENT PRIMARY KEY,
  subject_code VARCHAR(50) NOT NULL,
  start_time DATETIME NOT NULL,
  end_time DATETIME NOT NULL,
  dept_code VARCHAR(10) NOT NULL,  -- Which department exam belongs to
  status ENUM('pending','allocating','done','failed') DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Allocations (Seat assignment)
CREATE TABLE allocations (
  alloc_id INT AUTO_INCREMENT PRIMARY KEY,
  exam_id INT NOT NULL,
  usn VARCHAR(20) NOT NULL,
  classroom_id INT NOT NULL,
  bench_no INT NOT NULL,
  seat_pos INT NOT NULL,
  allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (exam_id) REFERENCES exam_sessions(exam_id) ON DELETE CASCADE,
  FOREIGN KEY (usn) REFERENCES student_details(usn) ON DELETE CASCADE,
  FOREIGN KEY (classroom_id) REFERENCES classroom_details(classroom_id),
  UNIQUE(exam_id, usn)
);

SHOW TABLES;-- 

INSERT INTO student_details (usn, name, dept_code)
VALUES
('1RV23CS001', 'Aarav Kumar', 'CSE'),
('1RV23CS002', 'Manan Joshi', 'CSE'),
('1RV23CS003', 'Priya Reddy', 'CSE'),

('1RV23CD001', 'Ritika Sharma', 'CD'),
('1RV23CD002', 'Aditya Rao', 'CD'),

('1RV23CY001', 'Ishaan Patel', 'CY'),
('1RV23CY002', 'Neha Iyer', 'CY');

INSERT INTO classroom_details (classroom_name, dept_code, no_of_benches, bench_capacity, location)
VALUES
('CSE-101', 'CSE', 10, 2, 'Block A, Floor 1'),
('CSE-102', 'CSE', 8, 2, 'Block A, Floor 1'),
('CD-201', 'CD', 6, 2, 'Block B, Floor 2'),
('CY-301', 'CY', 5, 2, 'Block C, Floor 3');

INSERT INTO exam_sessions (subject_code, start_time, end_time, dept_code)
VALUES
('CS101', '2025-11-01 09:00:00', '2025-11-01 12:00:00', 'CSE'),
('CD102', '2025-11-01 13:00:00', '2025-11-01 16:00:00', 'CD'),
('CY103', '2025-11-02 09:00:00', '2025-11-02 12:00:00', 'CY');




SELECT s.name, s.dept_code, e.subject_code, e.start_time
FROM student_details s
JOIN exam_sessions e ON s.dept_code = e.dept_code;

SELECT * FROM student_details;

ALTER TABLE exam_sessions 
MODIFY exam_id INT NOT NULL ;
