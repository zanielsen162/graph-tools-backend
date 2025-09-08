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
from services.db import authenticate, get_db_connection, create_user_db, checking_user_exist

dbr = Blueprint('dbr', __name__)

load_dotenv()


@dbr.route('/check_username', methods=['POST'])
def check_username():
    data = request.get_json()
    username = data.get('username', None)
    email = data.get('email', None)

    row = checking_user_exist(username, email)

    if row:
        response = jsonify({'msg': 'Username and/or email already taken', 'status': 401})
    else:
        response = jsonify({'msg': 'Username available', 'status': 200})
    
    return response

@dbr.route('/create_user', methods=['POST'])
def create_user():
    data = request.get_json()
    username = data.get('username', None)
    password = generate_password_hash(data.get('password', None))
    userId = uuid.uuid4()
    email = data.get('email', None)

    response = create_user_db(
        username=username,
        password=password,
        userId=userId,
        email=email
    )

    return response

@dbr.route('/fetch_posts', methods=['GET'])
def fetch_posts():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            """
            SELECT * FROM blog;
            """
        )

        entries = cur.fetchall()

        cur.close()
        conn.close()

        return entries
    except Exception as e:
        return []


@dbr.route('/post_graph', methods=['POST'])
def post_graph():
    res = request.get_json()

    userId = res['user']['id']
    username = res['user']['username']
    graphId = res['id']

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor) 

        query = sql.SQL("""
            INSERT INTO blog (
                name, username, vertex_set_size, edge_set_size, directed, acyclic,
                connected, complete, bipartite, tournament,
                induced_structures, notes, nodes, edges
            )
            SELECT
                name, %s,
                vertex_set_size, edge_set_size, directed, acyclic,
                connected, complete, bipartite, tournament,
                induced_structures, notes, nodes, edges
            FROM {user_table}
            WHERE id = %s
        """).format(user_table=sql.Identifier(str(userId)))

        cur.execute(query, (username, graphId))

        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'msg': 'successfully posted', 'status': 200})
    except Exception as e:
        print(e)
        return jsonify({'msg': 'save failed', 'status': 400})


# @dbr.route('/save_graph', methods=['POST'])
# def save_graph():
