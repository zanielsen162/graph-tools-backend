import os
import psycopg2 as psy
from dotenv import load_dotenv
import uuid
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

conn = psy.connect(
    host=os.getenv('DB_HOST'),
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USERNAME'),
    password=os.getenv('DB_PASSWORD')
)

cur = conn.cursor()

cur.execute('DROP TABLE IF EXISTS users;')
cur.execute(
    'CREATE TABLE users ('
        'user_id UUID PRIMARY KEY,'
        'username VARCHAR(50) UNIQUE NOT NULL,'
        'email VARCHAR(255) UNIQUE NOT NULL,'
        'password_hash VARCHAR(255) NOT NULL,'
        'created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,'
        'last_login TIMESTAMP WITH TIME ZONE'
    ');'
)

userId = uuid.uuid4()
password = generate_password_hash('password')

cur.execute(
    'INSERT INTO users (user_id, username, email, password_hash)'
    'VALUES (%s, %s, %s, %s)',
    (
        str(userId),
        'testuser',
        'testuser@fake.com',
        password
    )
)

conn.commit()

cur.close()
conn.close()