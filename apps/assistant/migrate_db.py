import sqlite3
import os

db_path = "apps/assistant/assistant.db"

if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Ajouter la colonne updated_at si elle n'existe pas
        cursor.execute("ALTER TABLE assistant_sessions ADD COLUMN updated_at DATETIME")
        conn.commit()
        conn.close()
        print("Success: Column updated_at added to assistant_sessions.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Info: Column updated_at already exists.")
        else:
            print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
else:
    print(f"Info: Database {db_path} not found. It will be created on next startup.")
