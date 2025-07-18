import networkx as nx
import matplotlib.pyplot as plt
import logging
import numpy as np
import copy
from abc import ABC, abstractmethod

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('sivista_app')

class LeafNodeAdder(ABC):
    def __init__(self, graph, start_node):
        self.graph = graph
        self.start = start_node
    @abstractmethod
    def getLeafNodes(self):
        pass
    def addDummyLeafNode(self, leaf_node_name=None):
        if leaf_node_name:    
            leaf_nodes = self.getLeafNodes()
            self.graph.add_node(leaf_node_name)
            logger.debug(f"Leaf Nodes Detected : {leaf_nodes}")
            for leaf_node in leaf_nodes:
                self.graph.add_edges_from([(leaf_node, leaf_node_name)])
        return self.graph

class GTSLeafNodeAdder(LeafNodeAdder):
    def __init__(self, graph, start_node):
        super().__init__(graph, start_node)
    def getLeafNodes(self):
        bfs_tree = nx.bfs_tree(self.graph, self.start)  # BFS traversal tree from start node
        leaf_nodes = [node for node in bfs_tree.nodes if bfs_tree.degree[node] == 1 and node != self.start]
        return leaf_nodes

class GTSGraphSetup(ABC):
    def __init__(self, graph_obj, edge_predictions, root_node, add_dummy_leaf = None, resistance_default = 0.00000001):
        self.graph = GTSLeafNodeAdder(copy.deepcopy(graph_obj), root_node).addDummyLeafNode(leaf_node_name=add_dummy_leaf)
        self.add_edge_weights(edge_predictions, resistance_default)
        self.start = root_node
        self.end = add_dummy_leaf

    def add_edge_weights(self, edge_predictions, resistance_default):
        
        if len(edge_predictions)==0:
            return
        edges1 = [f'{u}_to_{v}' for u, v in self.graph.edges()]
        edges2 = [f'{v}_to_{u}' for u, v in self.graph.edges()]
        edge_dict = {
            elem['edge']: elem['resistance'] for elem in edge_predictions
        }
        edge_weights = []
        self.edge_labels = {}
        for i in range(len(edges1)):
            e1, e2, val = None, None, None
            if edges1[i] in edge_dict:
                edge_weights.append(edge_dict[edges1[i]])
                e1, e2, val = edges1[i].split('_to_')[0], edges1[i].split('_to_')[1], edge_dict[edges1[i]]
            if edges2[i] in edge_dict:
                edge_weights.append(edge_dict[edges2[i]])    
                e1, e2, val = edges2[i].split('_to_')[0], edges2[i].split('_to_')[1], edge_dict[edges2[i]]
            if edges1[i] not in edge_dict and edges2[i] not in edge_dict:
                e1, e2, val = edges2[i].split('_to_')[0], edges2[i].split('_to_')[1], resistance_default
            self.edge_labels[(e1, e2)] = val
        for edge, val in self.edge_labels.items():
            self.graph.edges[edge]['resistance'] = val

    def visualizeGraph(self):
        pos = nx.circular_layout(self.graph) # Other layouts: planar_layout, random_layout, spectral_layout, spring_layout, shell_layout
        nx.draw(self.graph, pos, with_labels=True, node_color='skyblue', node_size=1500, edge_color='gray')
        nx.draw_networkx_edge_labels(
            self.graph, pos,
            edge_labels=self.edge_labels,
            font_color='red'
        )
        plt.show()

class EquivalentResistance(ABC):
    def __init__(self, graph_obj, edge_predictions={}, start_node=None, end_node=None):
        graphObj = GTSGraphSetup(graph_obj, edge_predictions, start_node, add_dummy_leaf="DUMMY_GROUND")
        self.graph = graphObj.graph
        self.start = graphObj.start
        self.end = graphObj.end
        

    def addWeights(self, resistance_default = 0.00000001):
        edge_weight = {}
        #invert the values and add them as weight
        for u,v,data in self.graph.edges(data=True):
            if 'resistance' in data:
                edge_weight[(u,v)] = 1/data['resistance']
            else:
                edge_weight[(u,v)] = 1/resistance_default
        nx.set_edge_attributes(self.graph, values = edge_weight, name = 'weight')

    def getResistance(self):
        logger.debug(f"Getting resisistance between {self.start} and {self.end}")
        self.addWeights()
        node_indexing = {node: index for index, node in enumerate(self.graph.nodes)}
        start_index , end_index = node_indexing[self.start], node_indexing[self.end]

        L = nx.laplacian_matrix(self.graph).toarray()
        L = np.delete(np.delete(L, end_index, axis=0), end_index, axis=1)
        M = np.zeros((len(L),1))
        M[start_index][0] = 1

        # Compute the Moore-Penrose pseudo-inverse of L
        L_pinv = np.linalg.pinv(L)
        L_pinv = np.matmul(L_pinv, M)
        vals = L_pinv.flatten()
        vals = np.insert(vals, end_index, 0)
        logger.debug(f"Equivalent resisistance between {self.start} and {self.end} is {vals[start_index]}")
        return round(vals[start_index], 2)