"""
Migration script to add watched_shows column to users table.
Run this script to update your existing database.
"""
import sqlite3
import os
from pathlib import Path

def migrate_database():
    # Find the database file
    db_path = Path(__file__).parent / 'instance' / 'pocketverse.db'
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        print("The database will be created automatically on next app start.")
        return
    
    print(f"Migrating database at {db_path}...")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'watched_shows' in columns:
            print("Column 'watched_shows' already exists. Migration not needed.")
            conn.close()
            return
        
        # Add the column
        print("Adding 'watched_shows' column to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN watched_shows TEXT")
        conn.commit()
        
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()

