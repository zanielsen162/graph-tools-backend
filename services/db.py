import os
import psycopg2 as psy
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, redirect, render_template, session, url_for, request, jsonify

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