
import sqlite3
from pathlib import Path

# location of the current project
BASE_DIR = Path(__file__).parent

# Definingwhere our database will be stored
DATABASE_PATH = BASE_DIR / "data" / "expenses.db"


def get_connection():
    """Create and return a database connection."""

    
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Connect to the SQLite database
    connection = sqlite3.connect(DATABASE_PATH)

    #foreign key protection
    connection.execute("PRAGMA foreign_keys = ON")

    # Returns rows as dictionaries-like objects
    connection.row_factory = sqlite3.Row

    return connection

def create_tables():
    """Create the users and expenses database tables."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # expense table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                spent_on TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
            )
        """)

        connection.commit()

    finally:
        connection.close()
