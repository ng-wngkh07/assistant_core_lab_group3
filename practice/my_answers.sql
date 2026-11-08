-- Practice SQL answers on school.db (Q1–Q15)

-- Q1
SELECT * FROM students;

-- Q2
SELECT name, year FROM students;

-- Q3
SELECT name FROM students WHERE program = 'CS';

-- Q4
SELECT name, year FROM students WHERE year >= 3;

-- Q5
SELECT name FROM students ORDER BY name DESC;

-- Q6
SELECT title, credits FROM courses WHERE credits = 4 ORDER BY title;

-- Q7
SELECT COUNT(*) FROM students;

-- Q8
SELECT program, COUNT(*) FROM students GROUP BY program ORDER BY program;

-- Q9
SELECT ROUND(AVG(grade), 2) FROM enrollments WHERE course_code = 'CSC10004';

-- Q10
SELECT student_id, course_code FROM enrollments WHERE grade IS NULL ORDER BY student_id;

-- Q11
SELECT s.name, e.grade
FROM enrollments e
JOIN students s ON s.id = e.student_id
WHERE e.course_code = 'CSC10014' AND e.grade IS NOT NULL
ORDER BY s.name;

-- Q12
SELECT c.title, COUNT(e.student_id)
FROM courses c
JOIN enrollments e ON e.course_code = c.code
GROUP BY c.code, c.title
ORDER BY COUNT(e.student_id) DESC, c.title;

-- Q13
SELECT DISTINCT s.name
FROM students s
JOIN enrollments e ON e.student_id = s.id
WHERE e.grade < 5
ORDER BY s.name;

-- Q14
SELECT s.name, SUM(c.credits) AS credits
FROM enrollments e
JOIN students s ON s.id = e.student_id
JOIN courses c ON c.code = e.course_code
GROUP BY s.id, s.name
ORDER BY credits DESC, s.name;

-- Q15
SELECT s.name
FROM students s
LEFT JOIN enrollments e ON e.student_id = s.id AND e.course_code = 'CSC10014'
WHERE e.student_id IS NULL
ORDER BY s.name;
