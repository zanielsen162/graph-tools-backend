import os
import psycopg2 as psy
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, redirect, render_template, session, url_for, request, jsonify
from psycopg2 import sql


from flask import Blueprint, jsonify

dbr = Blueprint('dbr', __name__)

load_dotenv()

def get_db_connection():
    conn = psy.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USERNAME'),
        password=os.getenv('DB_PASSWORD')
    )

    return conn

def checking_user_exist(username, email):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT user_id, username, email FROM users WHERE username = %s OR email = %s LIMIT 1;', (username,email))
        row = cur.fetchone()
        print(row)
        cur.close()
        conn.close()

        return row
    
    except Exception as e:
        response = jsonify({'msg': 'Error checking username', 'error': str(e), 'status': 500})
        return None
    
def create_user_db(username, userId, email, password=''):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            """
            INSERT INTO users (user_id, username, email, password_hash)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id) DO NOTHING
            """,
            (str(userId), username, email, password)
        )

        cur.execute(
            sql.SQL("""
                CREATE TABLE IF NOT EXISTS {} (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255),
                    vertex_set_size INT NOT NULL,
                    edge_set_size INT NOT NULL,
                    directed BOOLEAN NOT NULL,
                    acyclic BOOLEAN NOT NULL,
                    connected BOOLEAN NOT NULL,
                    complete BOOLEAN NOT NULL,
                    bipartite BOOLEAN NOT NULL,
                    tournament BOOLEAN NOT NULL,
                    induced_structures JSONB NOT NULL,
                    nodes JSONB,
                    edges JSONB
                );
            """).format(sql.Identifier(str(userId)))
        )

        conn.commit()
        response = jsonify({'msg': 'User created', 'status': 200})

    except Exception as e:
        conn.rollback()
        print("Error creating user:", e)
        response = jsonify({'msg': 'Error creating user', 'status': 401})
    
    finally:
        cur.close()
        conn.close()

    return response



def authenticate(input_id, input_password):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT user_id, username, email, password_hash
            FROM users
            WHERE username = %s OR email = %s
            """,
            (input_id, input_id)
        )
        user = cur.fetchone()
    except:
        response = jsonify({'msg': 'Connection error', 'status': 500})

    if user:
        if check_password_hash(user['password_hash'], input_password):
            response = jsonify(
                {
                    'status': 200, 
                    'user': {
                        'id': user['user_id'],
                        'username': user['username'],
                        'email': user['email'],
                        'auth_source': 'direct'
                    }
                }
            )
        else:
            response = jsonify({'msg': 'Invalid credentials', 'status': 401})
    else:
        response = jsonify({'msg': 'User not found', 'status': 401})
    return response