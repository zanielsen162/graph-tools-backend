import os
import psycopg2 as psy
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import uuid
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, redirect, render_template, session, url_for, request, jsonify
import json
from psycopg2 import sql

from flask import Blueprint, jsonify
from services.db import authenticate, get_db_connection

dbr = Blueprint('dbr', __name__)

load_dotenv()


@dbr.route('/check_username', methods=['POST'])
def check_username():
    data = request.get_json()
    username = data.get('username', None)
    email = data.get('email', None)

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT 1 FROM users WHERE username = %s OR email = %s LIMIT 1;', (username,email))
        row = cur.fetchone()
        if row:
            response = jsonify({'msg': 'Username and/or email already taken', 'status': 401})
        else:
            response = jsonify({'msg': 'Username available', 'status': 200})
        
        cur.close()
        conn.close()

    except Exception as e:
        response = jsonify({'msg': 'Error checking username', 'error': str(e), 'status': 500})
    
    return response

@dbr.route('/create_user', methods=['POST'])
def create_user():
    data = request.get_json()
    username = data.get('username', None)
    password = generate_password_hash(data.get('password', None))
    userId = uuid.uuid4()
    email = data.get('email', None)

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            'INSERT INTO users (user_id, username, email, password_hash) '
            'VALUES (%s, %s, %s, %s)',
            (str(userId), username, email, password)
        )

        cur.execute(
            sql.SQL("""
                CREATE TABLE {} (
                    id SERIAL PRIMARY KEY,
                    vertex_set_size INT NOT NULL,
                    edge_set_size INT NOT NULL,
                    directed BOOLEAN NOT NULL,
                    acyclic BOOLEAN NOT NULL,
                    connected BOOLEAN NOT NULL,
                    complete BOOLEAN NOT NULL,
                    bipartite BOOLEAN NOT NULL,
                    tournament BOOLEAN NOT NULL,
                    induced_structures JSONB NOT NULL
                    nodes JSONB
                    edges JSONB
                );
            """).format(sql.Identifier(str(userId)))
        )

        conn.commit()
        cur.close()
        conn.close()

        response = jsonify({'msg': 'User created', 'status': 200})

    except:
        response = jsonify({'msg': 'Error creating user', 'status': 401})


    return response

# @dbr.route('/save_graph', methods=['POST'])
# def save_graph():
