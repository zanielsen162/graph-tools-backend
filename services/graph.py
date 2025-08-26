import networkx as nx
from random import shuffle, sample, randint, random, randrange, choice
from itertools import combinations, product

def build_structure(type, n):
    match type:
        case 'pn':
            G = nx.path_graph(n)
        case 'kn':
            G = nx.complete_graph(n)
        case 'cn':
            G = nx.cycle_graph(n)
        case 'sn':
            G = nx.star_graph(n)
        case 'wn':
            G = nx.wheel_graph(n)
        case _:
            G = nx.Graph()
    return G

def add_bipartite(G,H):
    offset = max(G.nodes, default=-1) + 1
    H = nx.relabel_nodes(H, lambda x: x + offset)


    part0, part1 = nx.bipartite.sets(H)
    for i in part0:
        G.add_node(i, bipartite=0)
    for j in part1:
        G.add_node(j, bipartite=1)

    G.add_edges_from(H.edges())

    return G, H

def extend_acyclic_bipartite(G, H):
    G, H = add_bipartite(G, H)

    connect_from_G = None if nx.is_empty(G) else sample(list(G.nodes), 1)[0]
    connect_from_H = sample(list(H.nodes), 1)[0]

    if connect_from_G is not None:
        if G.nodes[connect_from_G]['bipartite'] != G.nodes[connect_from_H]['bipartite']:
            G.add_edge(connect_from_G,connect_from_H)
            if not len(list(nx.simple_cycles(G))) == 0:
                G.remove_edge(connect_from_G,connect_from_H)

    return G

def extend_acyclic(G, H):
    u = sample(list(H.nodes), 1)[0]
    v = None if nx.is_empty(G) else sample(list(G.nodes), 1)[0]

    offset = len(G)
    u += offset

    G = nx.disjoint_union(G, H)
    if v is not None:
        G.add_edge(u,v)
        if not len(list(nx.simple_cycles(G))) == 0:
            G.remove_edge(u,v)
    
    return G

def extend_bipartite(G, H):
    G, H = add_bipartite(G,H)

    connect_from_G = sample(list(G.nodes), randint(0, len(list(G.nodes))))
    connect_from_H = sample(list(H.nodes), randint(0, len(list(H.nodes))))

    for u in connect_from_G:
        for v in connect_from_H:
            if G.nodes[u]['bipartite'] != G.nodes[v]['bipartite']:
                G.add_edge(u,v)
    
    return G

def make_connected(G, bipartite=False, acyclic=False):
    components = [set(c) for c in nx.connected_components(G)]
    for comp in nx.connected_components(G):
        H = G.subgraph(comp)

        is_bip = nx.is_bipartite(H)
        is_acy = nx.is_forest(H)

        if bipartite and is_bip:
            # assign 0/1 labels for this component
            color = nx.algorithms.bipartite.color(H)
            nx.set_node_attributes(G, color, "bipartite")

    if len(components) <= 1:
        return G

    reps = [next(iter(c)) for c in components]

    for i in range(len(reps) - 1):
        u = reps[i]
        v = reps[i + 1]

        if bipartite:
            v_choices = [node for node in components[i+1]
                        if G.nodes[node]["bipartite"] != G.nodes[u]["bipartite"]]
            if v_choices:
                v = choice(v_choices)
            else:
                # fallback: single-vertex component with same color, just pick any
                v = reps[i + 1]

        G.add_edge(u, v)

    return G

def build_undirected_graph(
    n,
    # m,
    connected,
    complete,
    acyclic,
    bipartite,
    structures
):
    graph_size = 0
    struct_graphs = []
    for struct in structures:
        if not struct.free:
            for i in range(struct.amount):
                struct_graphs.append(build_structure(struct.structure.value, struct.size))
                graph_size += struct.size
    
    if graph_size < n:
        extend_by = n - graph_size
        if acyclic:
            num_trees = randint(1, extend_by)
            sizes = [1] * num_trees
            for _ in range(extend_by - num_trees):
                sizes[randrange(num_trees)] += 1
            for size in sizes:
                T = nx.generators.random_unlabeled_tree(size)
                struct_graphs.append(T)

        elif bipartite:
            top_size = extend_by // 2
            bottom_size = extend_by - top_size
            B = nx.algorithms.bipartite.random_graph(top_size, bottom_size, 0.5)
            struct_graphs += [
                B.subgraph(comp_nodes).copy()
                for comp_nodes in nx.connected_components(B)
            ]

        else:
            extended_graph = nx.gnp_random_graph(extend_by, 0.2)
            struct_graphs += [
                extended_graph.subgraph(comp_nodes).copy()
                for comp_nodes in nx.connected_components(extended_graph)
            ]


    G = nx.Graph()

    if acyclic and bipartite:
        for H in struct_graphs:
            G = extend_acyclic_bipartite(G, H)   

    elif acyclic:
        for H in struct_graphs:
            G = extend_acyclic(G, H)

    elif bipartite:
        for H in struct_graphs:
            G = extend_bipartite(G, H)

    elif complete:
        G = nx.complete_graph(n)
    
    else:
        for H in struct_graphs:
            G = nx.disjoint_union(G, H)

    if connected and nx.is_empty(G) or connected and not nx.is_connected(G):
        G = make_connected(G, bipartite, acyclic)

    return G

# Returns true if any of the given graphs are identified
def contains_induced(G, induced_graphs):
    for H in induced_graphs:
        if nx.algorithms.isomorphism.GraphMatcher(G, H).subgraph_is_isomorphic():
            return True
    return False

def generate_free_graph(n, induced_graphs, density=0.8, m=None, max_tries=1000):
    if m is None:
        m = density * n * (n-1) / 2

    induced_graphs = [build_structure(item.structure.value, item.size) for item in induced_graphs]

    G = nx.empty_graph(n)
    potential_edges = [(u,v) for u in range(n) for v in range (u+1, n)]
    shuffle(potential_edges)

    selector = 0
    attempts = 0

    while attempts < max_tries * len(potential_edges):
        if selector >= len(potential_edges):
            shuffle(potential_edges)
            selector = 0

        u,v = potential_edges[selector]
        if not G.has_edge(u,v):
            G.add_edge(u,v)
            if contains_induced(G, induced_graphs):
                G.remove_edge(u,v)
                break
            
        attempts += 1
        selector += 1           
    
    return G    

def generate_free_and_add(n, free_graphs, induced_graphs, density=0.8, m=None, max_tries=100):
    # begin by creating a free graph
    induced_graphs = [build_structure(item.structure.value, item.size) for item in induced_graphs]

    freed = [build_structure(item.structure.value, item.size) for item in free_graphs]
    
    G = generate_free_graph(n, free_graphs, m=m, density=density, max_tries=max_tries)

    # then, will try adding the induced graphs until they preserve the free structures as well
    for H in induced_graphs:
        offset = max(G.nodes, default=-1) + 1
        H = nx.relabel_nodes(H, lambda x: x + offset)

        connect_from_G = sample(list(G.nodes), randint(0, len(list(G.nodes))))
        connect_from_H = sample(list(H.nodes), randint(0, len(list(H.nodes))))
        G = nx.disjoint_union(G,H)

        for u in connect_from_H:
            for v in connect_from_G:
                G.add_edge(u, v)
                
                if contains_induced(G, freed):
                    G.remove_edge(u, v)

    return G


def export_graph_to_cytoscape_format(G):
    data = {
        "nodes": [{"data": {"id": str(node)}} for node in G.nodes()],
        "edges": [
            {"data": {
                "id": f"{u}{v}",
                "source": str(u),
                "target": str(v)
            }}
            for u, v in G.edges()
        ]
    }
    return data

# G = nx.Graph()
# G.add_nodes_from([0,1,2], bipartite=0)
# G.add_nodes_from([3,4], bipartite=1)
# G.add_edges_from([(0,3),(1,4)])


# H1 = Struct(False, StructType('pn', 'Path'), 4)
# # H2 = Struct(False, StructType('cn', 'Cycle'), 4)
# H3 = Struct(False, StructType('sn', 'Cycle'), 5)

# G = build_undirected_graph(20, True, False, True, True, [H1, H3])
# print('Contains structs?', contains_induced(G, [H1, H3]))
# acyclic = len(list(nx.simple_cycles(G))) == 0
# print('Is Acyclic?', acyclic)
# if not acyclic:
#     for val in list(nx.simple_cycles(G)):
#         print(val)