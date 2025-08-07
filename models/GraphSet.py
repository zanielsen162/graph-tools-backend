from user import User
from graph import Graph
from typing import List

class GraphSet:
    def __init__(self, user: User, graphs: List[Graph]):
        self.user = user
        self.graphs = graphs