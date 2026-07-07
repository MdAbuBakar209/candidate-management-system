from database import get_connection

def create_table():

    conn = get_connection()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS candidates(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        full_name TEXT NOT NULL, 

        email TEXT UNIQUE NOT NULL,

        mobile TEXT UNIQUE NOT NULL,

        department TEXT NOT NULL,

        percentage REAL NOT NULL,

        active_backlog TEXT NOT NULL,

        preferred_tech TEXT NOT NULL,

        skills TEXT,

        eligibility_status TEXT,

        round1_score INTEGER DEFAULT 0,

        final_shortlist_status TEXT DEFAULT 'Pending'
    )
    """)

    conn.commit()
    conn.close()