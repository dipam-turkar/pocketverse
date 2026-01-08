"""
Migration script to add episode_tag and show_name columns to posts table.
Run this script to update the database schema.
"""
import sqlite3
import os

# Define the path to your database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'pocketverse.db')

def migrate_add_episode_tagging():
    print(f"Migrating database at {DB_PATH}...")
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check existing columns
        cursor.execute("PRAGMA table_info(posts)")
        columns = [info[1] for info in cursor.fetchall()]
        print(f"Existing columns: {columns}")

        # Add show_name column if it doesn't exist
        if 'show_name' not in columns:
            print("Adding 'show_name' column to posts table...")
            cursor.execute("ALTER TABLE posts ADD COLUMN show_name VARCHAR(200);")
            conn.commit()
            print("✅ 'show_name' column added successfully.")
        else:
            print("ℹ️ 'show_name' column already exists. No migration needed.")

        # Add episode_tag column if it doesn't exist
        if 'episode_tag' not in columns:
            print("Adding 'episode_tag' column to posts table...")
            cursor.execute("ALTER TABLE posts ADD COLUMN episode_tag INTEGER;")
            conn.commit()
            print("✅ 'episode_tag' column added successfully.")
        else:
            print("ℹ️ 'episode_tag' column already exists. No migration needed.")

        # Create indexes for better query performance
        print("Creating indexes...")
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_show_name ON posts(show_name);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_episode_tag ON posts(episode_tag);")
            conn.commit()
            print("✅ Indexes created successfully.")
        except sqlite3.Error as e:
            print(f"⚠️ Index creation warning (may already exist): {e}")

        print("✅ Migration completed successfully!")

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    migrate_add_episode_tagging()

