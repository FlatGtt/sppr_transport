import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.database import get_connection

def setup_database():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS objects (
            id INTEGER PRIMARY KEY,
            type TEXT NOT NULL,
            mtbf REAL NOT NULL,
            mttr REAL NOT NULL,
            availability REAL
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id SERIAL PRIMARY KEY,
            object_id INTEGER REFERENCES objects(id),
            event_type TEXT CHECK (event_type IN ('failure', 'repair')),
            time REAL NOT NULL
        );
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Таблицы успешно созданы.")

if __name__ == "__main__":
    setup_database()
