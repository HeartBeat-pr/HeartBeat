# All doctors will have password: doctor123

import mysql.connector
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

db = mysql.connector.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', ''),
    database=os.getenv('DB_NAME', 'heartbeat_db')
)

cursor = db.cursor()
hashed = bcrypt.hashpw('doctor123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

for doctor_id in range(1, 6):
    cursor.execute("UPDATE doctors SET password = %s WHERE id = %s", (hashed, doctor_id))

db.commit()
cursor.close()
db.close()

print("All doctor passwords set to: doctor123")
