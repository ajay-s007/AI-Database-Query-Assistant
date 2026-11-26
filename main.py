"""
AI DATABASE QUERY ASSISTANT
Student Project: AI-SD-006
Student Code: DAS014552

Run in Pydroid 3:
1. Save this file as main.py
2. Tap Run.
3. Type English questions such as:
   - show all students
   - show students from CSE
   - show students from Salem
   - show students older than 19
   - count students
   - show average age
   - show students in CSE department
   - add student Ajay age 19 department CSE city Salem
   - update student 1 city to Chennai
   - delete student 5

This is a beginner-friendly rule-based Natural Language-to-SQL system.
It uses Python, SQLite, regular expressions and intent/entity extraction.
It does not claim to be a trained machine-learning model.
"""

import sqlite3
import re
from datetime import datetime

DB_NAME = "ai_database_assistant.db"


# -------------------- DATABASE --------------------

def connect_db():
    return sqlite3.connect(DB_NAME)


def column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return column_name in [row[1] for row in cursor.fetchall()]


def setup_database():
    """Create tables and safely add missing columns to older databases."""
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            department_id INTEGER PRIMARY KEY AUTOINCREMENT,
            department_name TEXT UNIQUE NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            department TEXT,
            city TEXT
        )
    """)

    # Migration: fixes older databases that were created without city.
    if not column_exists(cur, "students", "city"):
        cur.execute("ALTER TABLE students ADD COLUMN city TEXT")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS query_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_question TEXT NOT NULL,
            generated_sql TEXT,
            created_at TEXT NOT NULL
        )
    """)

    departments = ["CSE", "ECE", "IT", "EEE", "MECH"]
    for dept in departments:
        cur.execute(
            "INSERT OR IGNORE INTO departments (department_name) VALUES (?)",
            (dept,)
        )

    cur.execute("SELECT COUNT(*) FROM students")
    if cur.fetchone()[0] == 0:
        sample_students = [
            ("Ajay", 19, "CSE", "Salem"),
            ("Arun", 20, "CSE", "Chennai"),
            ("Ravi", 19, "ECE", "Salem"),
            ("Kumar", 21, "IT", "Madurai"),
            ("Priya", 20, "EEE", "Coimbatore")
        ]
        cur.executemany("""
            INSERT INTO students (name, age, department, city)
            VALUES (?, ?, ?, ?)
        """, sample_students)

    conn.commit()
    conn.close()


# -------------------- DISPLAY --------------------

def display_rows(cursor):
    rows = cursor.fetchall()
    if not rows:
        print("\nNo records found.")
        return

    headers = [item[0] for item in cursor.description]
    widths = []
    for i, header in enumerate(headers):
        max_value = max([len(str(row[i])) for row in rows] + [len(header)])
        widths.append(min(max_value, 24))

    line = "+-" + "-+-".join("-" * width for width in widths) + "-+"
    print("\n" + line)
    print("| " + " | ".join(headers[i][:widths[i]].ljust(widths[i])
                          for i in range(len(headers))) + " |")
    print(line)
    for row in rows:
        print("| " + " | ".join(str(row[i])[:widths[i]].ljust(widths[i])
                              for i in range(len(headers))) + " |")
    print(line)
    print("Total records:", len(rows))


def save_history(question, sql):
    conn = connect_db()
    conn.execute("""
        INSERT INTO query_history (user_question, generated_sql, created_at)
        VALUES (?, ?, ?)
    """, (question, sql, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()


# -------------------- NLP PROCESSING --------------------

def normalize(text):
    return re.sub(r"\s+", " ", text.strip().lower())


def extract_department(text):
    match = re.search(r"\b(cse|ece|eee|it|mech|mechanical)\b", text, re.I)
    if not match:
        return None
    value = match.group(1).upper()
    return "MECH" if value == "MECHANICAL" else value


def extract_city(text):
    known_cities = [
        "salem", "chennai", "madurai", "coimbatore", "trichy",
        "tiruchirappalli", "virudhachalam", "cuddalore", "erode"
    ]
    for city in known_cities:
        if re.search(r"\b" + re.escape(city) + r"\b", text, re.I):
            return city.title()
    match = re.search(r"\bcity\s+(?:is\s+)?([a-z]+)\b", text, re.I)
    return match.group(1).title() if match else None


def extract_student_id(text):
    patterns = [
        r"\bstudent\s+(?:id\s*)?#?\s*(\d+)\b",
        r"\bid\s*#?\s*(\d+)\b",
        r"\b#(\d+)\b"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            return int(match.group(1))
    return None


def extract_age_condition(text):
    patterns = [
        (r"\b(?:older than|above|greater than)\s+(\d+)\b", ">"),
        (r"\b(?:younger than|below|less than)\s+(\d+)\b", "<"),
        (r"\b(?:at least|minimum)\s+(\d+)\b", ">="),
        (r"\b(?:at most|maximum)\s+(\d+)\b", "<="),
        (r"\bage\s*(?:is|=)?\s*(\d+)\b", "=")
    ]
    for pattern, operator in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            return operator, int(match.group(1))
    return None


def extract_new_student(text):
    # Example: add student Ajay age 19 department CSE city Salem
    match = re.search(
        r"\badd\s+(?:a\s+)?student\s+([a-z][a-z ]*?)\s+"
        r"(?:age\s+(\d+))\s+(?:department\s+([a-z]+))"
        r"(?:\s+city\s+([a-z ]+))?$",
        text.strip(),
        re.I
    )
    if not match:
        return None
    name = match.group(1).strip().title()
    age = int(match.group(2))
    dept = match.group(3).upper()
    city = (match.group(4) or "Unknown").strip().title()
    if dept == "MECHANICAL":
        dept = "MECH"
    return name, age, dept, city


# -------------------- QUERY GENERATION --------------------

def generate_query(question):
    text = normalize(question)

    # Schema information
    if any(word in text for word in ["show schema", "database schema", "table structure"]):
        return "SCHEMA", None, []

    # Query history
    if "history" in text or "previous queries" in text:
        return "HISTORY", None, []

    # Insert student
    if text.startswith("add ") or text.startswith("insert "):
        data = extract_new_student(text)
        if data:
            sql = """INSERT INTO students (name, age, department, city)
                     VALUES (?, ?, ?, ?)"""
            return "INSERT", sql, list(data)
        return "HELP", None, []

    # Update city / department / age
    if text.startswith("update ") or text.startswith("change "):
        student_id = extract_student_id(text)
        if student_id is None:
            return "HELP", None, []

        match = re.search(r"\b(?:city)\s+(?:to|as)\s+([a-z ]+)$", text, re.I)
        if match:
            return "UPDATE", "UPDATE students SET city = ? WHERE student_id = ?", [
                match.group(1).strip().title(), student_id
            ]

        match = re.search(r"\bdepartment\s+(?:to|as)\s+([a-z]+)\b", text, re.I)
        if match:
            return "UPDATE", "UPDATE students SET department = ? WHERE student_id = ?", [
                match.group(1).upper(), student_id
            ]

        match = re.search(r"\bage\s+(?:to|as)\s+(\d+)\b", text, re.I)
        if match:
            return "UPDATE", "UPDATE students SET age = ? WHERE student_id = ?", [
                int(match.group(1)), student_id
            ]
        return "HELP", None, []

    # Delete student
    if text.startswith("delete ") or text.startswith("remove "):
        student_id = extract_student_id(text)
        if student_id is not None:
            return "DELETE", "DELETE FROM students WHERE student_id = ?", [student_id]
        return "HELP", None, []

    # Aggregates
    if any(word in text for word in ["count", "how many", "total number"]):
        sql = "SELECT COUNT(*) AS total_students FROM students"
        params = []
        dept = extract_department(text)
        city = extract_city(text)
        if dept:
            sql += " WHERE department = ?"
            params.append(dept)
        elif city:
            sql += " WHERE city = ?"
            params.append(city)
        return "SELECT", sql, params

    if "average age" in text or "avg age" in text:
        return "SELECT", "SELECT AVG(age) AS average_age FROM students", []

    if "maximum age" in text or "oldest" in text:
        return "SELECT", "SELECT MAX(age) AS maximum_age FROM students", []

    if "minimum age" in text or "youngest" in text:
        return "SELECT", "SELECT MIN(age) AS minimum_age FROM students", []

    # JOIN
    if "join" in text or "department details" in text:
        sql = """
            SELECT students.student_id, students.name, students.age,
                   departments.department_name
            FROM students
            LEFT JOIN departments
            ON students.department = departments.department_name
        """
        return "SELECT", sql, []

    # General SELECT with filters
    sql = "SELECT student_id, name, age, department, city FROM students"
    conditions = []
    params = []

    dept = extract_department(text)
    city = extract_city(text)
    age_condition = extract_age_condition(text)

    if dept:
        conditions.append("department = ?")
        params.append(dept)

    if city:
        conditions.append("city = ?")
        params.append(city)

    if age_condition:
        operator, age = age_condition
        conditions.append("age " + operator + " ?")
        params.append(age)

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    if "sort" in text or "order" in text or "ascending" in text or "alphabetical" in text:
        sql += " ORDER BY name ASC"
    elif "descending" in text or "highest age" in text:
        sql += " ORDER BY age DESC"
    elif "youngest first" in text:
        sql += " ORDER BY age ASC"

    # Default show/list/search intent
    if any(word in text for word in [
        "show", "list", "display", "find", "search", "get",
        "student", "all", "who", "from"
    ]):
        return "SELECT", sql, params

    return "HELP", None, []


# -------------------- ASSISTANT --------------------

def show_schema():
    conn = connect_db()
    cur = conn.cursor()
    for table in ["students", "departments", "query_history"]:
        cur.execute(f"PRAGMA table_info({table})")
        print("\nTable:", table)
        for row in cur.fetchall():
            print(" -", row[1], "(" + row[2] + ")")
    conn.close()


def show_history():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT history_id, user_question, generated_sql, created_at
        FROM query_history ORDER BY history_id DESC LIMIT 10
    """)
    display_rows(cur)
    conn.close()


def process_question(question):
    intent, sql, params = generate_query(question)

    if intent == "HELP":
        print("\nI could not understand that question.")
        print("Try: show all students")
        print("Try: show students from CSE")
        print("Try: count students")
        print("Try: show students older than 19")
        print("Try: add student Ajay age 19 department CSE city Salem")
        return

    if intent == "SCHEMA":
        show_schema()
        save_history(question, "DISPLAY DATABASE SCHEMA")
        return

    if intent == "HISTORY":
        show_history()
        save_history(question, "DISPLAY QUERY HISTORY")
        return

    if intent in ["INSERT", "UPDATE", "DELETE"]:
        print("\nGenerated SQL:")
        print(sql)
        print("Parameters:", params)
        confirm = input("Confirm this change? (yes/no): ").strip().lower()
        if confirm not in ["yes", "y"]:
            print("Operation cancelled.")
            return

    conn = connect_db()
    cur = conn.cursor()

    try:
        print("\nDetected Intent:", intent)
        print("Generated SQL:")
        print(sql)
        if params:
            print("Parameters:", params)

        cur.execute(sql, params)

        if intent == "SELECT":
            display_rows(cur)
        else:
            conn.commit()
            print("\nOperation completed successfully.")
            print("Rows affected:", cur.rowcount)

        save_history(question, sql)

    except sqlite3.Error as error:
        print("\nDatabase error:", error)
        print("Please check the question and try again.")
    finally:
        conn.close()


def main():
    setup_database()

    print("=" * 55)
    print("       AI DATABASE QUERY ASSISTANT")
    print("=" * 55)
    print("Convert English questions into SQL queries.")
    print("Type 'help' for examples.")
    print("Type 'exit' to close the program.")

    while True:
        question = input("\nAsk your database question: ").strip()

        if question.lower() in ["exit", "quit", "bye"]:
            print("\nThank you for using AI Database Query Assistant!")
            break

        if question.lower() == "help":
            print("\nEXAMPLE QUESTIONS")
            print("1. show all students")
            print("2. show students from CSE")
            print("3. show students from Salem")
            print("4. show students older than 19")
            print("5. count students")
            print("6. show average age")
            print("7. show oldest student age")
            print("8. show students in alphabetical order")
            print("9. show department details")
            print("10. show database schema")
            print("11. show query history")
            print("12. add student Ajay age 19 department CSE city Salem")
            print("13. update student 1 city to Chennai")
            print("14. delete student 5")
            continue

        if not question:
            print("Please enter a question.")
            continue

        process_question(question)


if __name__ == "__main__":
    main()
