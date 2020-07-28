import logging
import os
import requests
import urllib3

from typing import List, Optional

from models.consts import *

from models.node import Node
from models.node_relation import NodeRelation

urllib3.disable_warnings()

_LOGGER = logging.getLogger(__name__)


class HAZWaveManager:
    token: str
    url: str
    ssl_key: Optional[str]
    ssl_certificate: Optional[str]
    is_ssl: bool
    is_ready: bool

    def __init__(self):
        self.url = os.environ.get('HA_URL')
        self.token = os.environ.get('HA_TOKEN')
        self.ssl_key = os.environ.get('SSL_KEY')
        self.ssl_certificate = os.environ.get('SSL_CERTIFICATE')

        if self.ssl_key == "":
            self.ssl_key = None

        if self.ssl_certificate == "":
            self.ssl_certificate = None

        self.is_ssl = self.ssl_key is not None and self.ssl_certificate is not None

        self.is_ready = True

        if self.url is None:
            _LOGGER.fatal("Environment variable HA_URL is empty, cannot initialize server")
            self.is_ready = False
            return

        if self.token is None:
            _LOGGER.fatal("Environment variable HA_URL is empty, cannot initialize server")
            self.is_ready = False
            return

        _LOGGER.info(f"Initializing server {SERVER_BIND}:{SERVER_PORT}, SSL: {self.is_ssl}")

    def get_states(self):
        try:
            headers = {
                'Authorization': 'Bearer ' + self.token
            }

            verify = False if "https://" in self.url else None

            response = requests.get(f"{self.url}/api/states", headers=headers, verify=verify)

            return response.json()

        except Exception as ex:
            _LOGGER.error(f"Failed to retrieve states from HA, error: {ex}")

            return None

    def get_zwave_states(self):
        states = self.get_states()
        items = []
        for state in states:
            entity_id = state.get("entity_id", "")

            if "zwave." in entity_id:
                items.append(state)

        return items

    @staticmethod
    def get_hub(nodes: List[Node]) -> Optional[Node]:
        for node in nodes:
            if node.isPrimary:
                return node

        return None

    @staticmethod
    def _get_node(nodes: List[Node], node_id: int) -> Optional[Node]:
        for node in nodes:
            if node.id == node_id:
                return node

        return None

    def _get_edges(self, node: Node, nodes: List[Node]) -> List[NodeRelation]:
        edges: List[NodeRelation] = []

        neighbors = node.neighbors

        if neighbors is None:
            hub = self.get_hub(nodes)

            if hub is not None:
                relation = NodeRelation()
                relation.id = node.id
                relation.toNodeId = hub.id

                edges.append(relation)
        else:
            for neighbor_id in neighbors:
                neighbor = self._get_node(nodes, neighbor_id)

                if neighbor is not None:
                    relation = NodeRelation()
                    relation.id = node.id
                    relation.toNodeId = neighbor.id

                    edges.append(relation)

        return edges

    def _get_zwave_nodes(self):
        zwave_states = self.get_zwave_states()
        result: List[Node] = []

        for entity in zwave_states:
            node = Node(entity)

            result.append(node)

        return result

    def update_hop(self, node: Node, nodes: List[Node]):
        current_hop = node.hop

        for edge in node.edges:
            to_node = self._get_node(nodes, edge.toNodeId)

            if to_node is not None:
                to_node_hop = to_node.hop

                if to_node_hop == -1 or to_node_hop > current_hop + 1:
                    to_node.hop = current_hop + 1

                    self.update_hop(to_node, nodes)

    def update_relation_parent(self, node: Node, nodes: List[Node]):
        for edge in node.edges:
            to_node = self._get_node(nodes, edge.toNodeId)

            edge_type = "child"
            if node.hop == to_node.hop:
                edge_type = "sibling"
            elif node.hop < to_node.hop:
                edge_type = "parent"

            edge.type = edge_type

    def get_zwave_nodes(self):
        nodes: List[Node] = self._get_zwave_nodes()
        first_hop_nodes = []
        for node in nodes:
            node.edges = self._get_edges(node, nodes)

            if node.hop > -1:
                first_hop_nodes.append(node)

        for node in first_hop_nodes:
            if node.hop > -1:
                self.update_hop(node, nodes)

        for node in nodes:
            self.update_relation_parent(node, nodes)

        return nodes

    def get_zwave_nodes_json(self):
        nodes = self.get_zwave_nodes()
        items = []

        for node in nodes:
            items.append(node.to_dict())

        return items

