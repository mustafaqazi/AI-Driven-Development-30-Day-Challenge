import sqlite3
import json
import os

DATABASE_NAME = 'study_agent.db'

def connect_db():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def create_tables(conn):
    """
    Creates necessary tables in the database if they do not already exist:
    - pdf_files: Stores metadata and extracted text of uploaded PDFs.
    - summaries: Stores generated summaries for PDFs.
    - quizzes: Stores generated quizzes for PDFs.
    - quiz_attempts: Stores user's quiz attempts and scores.
    """
    cursor = conn.cursor()

    # Table for PDF files
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pdf_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE NOT NULL,
            text_content TEXT NOT NULL,
            uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table for summaries
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pdf_id INTEGER NOT NULL,
            summary_text TEXT NOT NULL,
            summary_style TEXT,
            generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pdf_id) REFERENCES pdf_files (id)
        )
    ''')

    # Table for quizzes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pdf_id INTEGER NOT NULL,
            quiz_data TEXT NOT NULL, -- Stored as JSON
            generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pdf_id) REFERENCES pdf_files (id)
        )
    ''')

    # Table for quiz attempts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER NOT NULL,
            user_answers TEXT NOT NULL, -- Stored as JSON
            score INTEGER NOT NULL,
            attempted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id)
        )
    ''')

    conn.commit()

def insert_pdf_data(conn, filename, text_content):
    """Inserts or updates PDF file data into the database."""
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO pdf_files (filename, text_content) VALUES (?, ?)",
                       (filename, text_content))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        # If file already exists, update its content and return existing ID
        cursor.execute("UPDATE pdf_files SET text_content = ? WHERE filename = ?",
                       (text_content, filename))
        conn.commit()
        cursor.execute("SELECT id FROM pdf_files WHERE filename = ?", (filename,))
        return cursor.fetchone()['id']

def get_pdf_data(conn, filename):
    """Retrieves PDF data by filename."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pdf_files WHERE filename = ?", (filename,))
    return cursor.fetchone()

def get_pdf_data_by_id(conn, pdf_id):
    """Retrieves PDF data by ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pdf_files WHERE id = ?", (pdf_id,))
    return cursor.fetchone()

def insert_summary(conn, pdf_id, summary_text, summary_style="default"):
    """Inserts a generated summary for a PDF."""
    cursor = conn.cursor()
    cursor.execute("INSERT INTO summaries (pdf_id, summary_text, summary_style) VALUES (?, ?, ?)",
                   (pdf_id, summary_text, summary_style))
    conn.commit()
    return cursor.lastrowid

def get_summary(conn, pdf_id):
    """Retrieves the latest summary for a given PDF ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM summaries WHERE pdf_id = ? ORDER BY generated_at DESC LIMIT 1",
                   (pdf_id,))
    return cursor.fetchone()

def insert_quiz(conn, pdf_id, quiz_data):
    """Inserts a generated quiz (as JSON) for a PDF."""
    cursor = conn.cursor()
    quiz_json = json.dumps(quiz_data)
    cursor.execute("INSERT INTO quizzes (pdf_id, quiz_data) VALUES (?, ?)",
                   (pdf_id, quiz_json))
    conn.commit()
    return cursor.lastrowid

def get_quiz(conn, pdf_id):
    """Retrieves the latest quiz for a given PDF ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM quizzes WHERE pdf_id = ? ORDER BY generated_at DESC LIMIT 1",
                   (pdf_id,))
    quiz_row = cursor.fetchone()
    if quiz_row:
        quiz_data = json.loads(quiz_row['quiz_data'])
        return {**quiz_row, 'quiz_data': quiz_data}
    return None

def insert_quiz_attempt(conn, quiz_id, user_answers, score):
    """Inserts a user's quiz attempt and score."""
    cursor = conn.cursor()
    user_answers_json = json.dumps(user_answers)
    cursor.execute("INSERT INTO quiz_attempts (quiz_id, user_answers, score) VALUES (?, ?, ?)",
                   (quiz_id, user_answers_json, score))
    conn.commit()
    return cursor.lastrowid

if __name__ == '__main__':
    # Example usage (for testing database functions independently)
    conn = connect_db()
    create_tables(conn)
    print(f"Database '{DATABASE_NAME}' and tables ensured.")

    # You can add more testing code here if needed
    # For instance, to check if a DB file was created or tables exist.
    conn.close()
    print("Database connection closed.")
