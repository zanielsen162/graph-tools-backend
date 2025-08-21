from flask import Blueprint, request, jsonify
graph = Blueprint('graph', __name__)
from psycopg2.extras import RealDictCursor
from psycopg2 import sql
from services.db import get_db_connection
import json
import uuid

@graph.route('/save_graph', methods=["POST"])
def save_graph():
    res = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    userId = res['user']['id']
    vertex_set_size = res['formData']['size']['vertexSetSize']
    edge_set_size = res['formData']['size']['edgeSetSize']
    directed = res['formData']['types']['directed']
    acyclic = res['formData']['types']['acyclic']
    connected = res['formData']['types']['connected']
    complete = res['formData']['types']['complete']
    bipartite = res['formData']['types']['bipartite']
    tournament = res['formData']['types']['tournament']
    induced_structures = res['formData']['inducedStructures']
    nodes = res['nodes']
    edges = res['edges']

    cur.execute(
        sql.SQL("""
            INSERT INTO {} (
                vertex_set_size,
                edge_set_size,
                directed,
                acyclic,
                connected,
                complete,
                bipartite,
                tournament,
                induced_structures,
                nodes,
                edges
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """).format(sql.Identifier(str(userId))),
        (   
            vertex_set_size,
            edge_set_size,
            directed,
            acyclic,
            connected,
            complete,
            bipartite,
            tournament,
            json.dumps(induced_structures),
            json.dumps(nodes),
            json.dumps(edges)
        )
    )

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({'msg': 'save successful'})
