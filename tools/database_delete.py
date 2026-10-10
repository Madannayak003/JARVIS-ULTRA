import sqlite3
from pathlib import Path

db = Path("ai/memory.db")

print("Database:", db.resolve())

conn = sqlite3.connect(db)

cursor = conn.cursor()

cursor.execute("DELETE FROM memories WHERE id = ?", (34,))

conn.commit()

print("Rows deleted:", cursor.rowcount)

conn.close()

print("Done!")