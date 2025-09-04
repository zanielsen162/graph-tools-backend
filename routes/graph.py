from flask import Blueprint, request, jsonify
graph = Blueprint('graph', __name__)
from psycopg2.extras import RealDictCursor
from psycopg2 import sql
from services.db import get_db_connection
import json
from services.graph import build_undirected_graph, generate_free_graph, generate_free_and_add, export_graph_to_cytoscape_format
from models.Structure import StructType, Struct
import networkx as nx
from psycopg2.extras import RealDictCursor

@graph.route('/generate_graph', methods=['POST'])
def generate_graph_route():
    res = request.get_json()

    vertex_set_size = res['formData']['size']['vertexSetSize']
    edge_set_size = res['formData']['size']['edgeSetSize']
    directed = res['formData']['types']['directed']
    acyclic = res['formData']['types']['acyclic']
    connected = res['formData']['types']['connected']
    complete = res['formData']['types']['complete']
    bipartite = res['formData']['types']['bipartite']
    tournament = res['formData']['types']['tournament']
    induced_structures = res['formData']['inducedStructures']

    induced_structures = [
        Struct(
            free=item["free"],
            structure=StructType(
                value=item["structure"]["value"],
                label=item["structure"]["label"]
            ),
            size=item["size"],
            amount=item["amount"]
        )
        for item in induced_structures
    ]
    free_structs = [struct for struct in induced_structures if struct.free]
    include_structs = [struct for struct in induced_structures if not struct.free]

    if not directed:
        if len(free_structs) == 0:
            G = build_undirected_graph(
                n=vertex_set_size,
                complete=complete,
                acyclic=acyclic,
                bipartite=bipartite,
                structures=include_structs,
                connected=connected
            )
        elif len(include_structs) == 0:
            G = generate_free_graph(
                n=vertex_set_size,
                induced_graphs=free_structs,
            )
        else:
            G = generate_free_and_add(
                n=vertex_set_size,
                induced_graphs=include_structs,
                free_graphs=free_structs,
                m=edge_set_size
            )
        return jsonify(
            export_graph_to_cytoscape_format(G)
        )
        

@graph.route('/save_graph', methods=["POST"])
def save_graph():
    res = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    userId = res['user']['id']
    name = res['formData']['name']
    vertex_set_size = res['formData']['size']['vertexSetSize']
    edge_set_size = res['formData']['size']['edgeSetSize']
    directed = res['formData']['types']['directed']
    acyclic = res['formData']['types']['acyclic']
    connected = res['formData']['types']['connected']
    complete = res['formData']['types']['complete']
    bipartite = res['formData']['types']['bipartite']
    tournament = res['formData']['types']['tournament']
    induced_structures = res['formData']['inducedStructures']
    nodes = res['graph']['nodes']
    edges = res['graph']['edges']

    cur.execute(
        sql.SQL("""
            INSERT INTO {} (
                name,
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
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """).format(sql.Identifier(str(userId))),
        (   
            name,
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

@graph.route('/load_graphs', methods=["POST"])
def load_graphs():
    res = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    userId = res['user']['id']
    cur.execute(f'SELECT * FROM "{userId}";')
    graphs = cur.fetchall()
    cur.close()
    conn.close()

    return graphs

@graph.route('/load_identifiers', methods=['POST'])
def load_identifiers():
    res = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    userId = res['user']['id']
    cur.execute(f'SELECT id, name FROM "{userId}";')
    graphs = cur.fetchall()
    cur.close()
    conn.close()

    return graphs

@graph.route('/update_graph', methods=['POST'])
def update_graph():
    res = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    userId = res['user']['id']
    graphId = res['analyzeFormData']['id']
    notes = res['analyzeFormData']['notes']
    
    query = f'UPDATE "{userId}" SET notes = %s WHERE id = %s;'
    cur.execute(query, (notes, graphId))

    conn.commit()
    
    cur.close()
    conn.close()

    return jsonify({"success": True, "updated": graphId})

@graph.route('/remove_graph', methods=['POST'])
def delete_graph():
    res = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    userId = res['user']['id']
    graphIds = res.get('id') 
    if not graphIds or not isinstance(graphIds, list):
        return jsonify({"success": False, "error": "No IDs provided"}), 400
    
    placeholders = ','.join(['%s'] * len(graphIds))
    query = f'DELETE FROM "{userId}" WHERE id IN ({placeholders});'
    cur.execute(query, graphIds)
    conn.commit()
    
    cur.close()
    conn.close()

    return jsonify({"success": True, "deleted_ids": graphIds})