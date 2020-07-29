import json
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
    def _get_hub(nodes: List[Node]) -> Optional[Node]:
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

    def _update_edges(self, node: Node, nodes: List[Node]):
        neighbors = node.neighbors

        if node.edges is None:
            node.edges = []

        if neighbors is None:
            hub = self._get_hub(nodes)

            if hub is not None:
                relation = NodeRelation()
                relation.id = node.id
                relation.toNodeId = hub.id

                # print(f"H {relation.id} --> {relation.toNodeId}")

                node.edges.append(relation)

                if hub.edges is None:
                    hub.edges = []

                should_created_op = True
                for neighbor_edge in hub.edges:
                    if neighbor_edge.toNodeId == node.id:
                        should_created_op = False

                if should_created_op:
                    op_relation = NodeRelation()
                    op_relation.id = hub.id
                    op_relation.toNodeId = node.id

                    # print(f"H> {op_relation.id} --> {op_relation.toNodeId}")

                    hub.edges.append(op_relation)
        else:
            for neighbor_id in neighbors:
                neighbor = self._get_node(nodes, neighbor_id)

                if neighbor is not None:
                    relation = NodeRelation()
                    relation.id = node.id
                    relation.toNodeId = neighbor.id

                    # print(f"{relation.id} --> {relation.toNodeId}")

                    node.edges.append(relation)

                    if neighbor.edges is None:
                        neighbor.edges = []

                    should_created_op = True
                    for neighbor_edge in neighbor.edges:
                        if neighbor_edge.toNodeId == node.id:
                            should_created_op = False

                    if should_created_op:
                        op_relation = NodeRelation()
                        op_relation.id = neighbor.id
                        op_relation.toNodeId = node.id

                        # print(f"> {op_relation.id} --> {op_relation.toNodeId}")

                        neighbor.edges.append(op_relation)

    def _get_zwave_nodes(self):
        zwave_states = self.get_zwave_states()
        result: List[Node] = []

        for entity in zwave_states:
            node = Node(entity)

            result.append(node)

        return result

    def _update_hop(self, hop: int, nodes: List[Node]) -> bool:
        result = False
        hop_nodes = []

        for node in nodes:
            if node.hop == hop:
                hop_nodes.append(node)

                result = True

        for node in hop_nodes:
            current_hop = node.hop
            sub_nodes: List[Node] = []

            # print(f"{node.id} >> {node.hop}")

            for edge in node.edges:
                to_node = self._get_node(nodes, edge.toNodeId)

                # print(f">> {to_node.id} >> {to_node.hop}")

                if to_node is not None and to_node.hop == -1:
                    to_node.hop = current_hop + 1

                    # print(f">> {to_node.id} >> {to_node.hop}")

                    sub_nodes.append(to_node)

        return result

    def _update_relation_type(self, node: Node, nodes: List[Node]):
        for edge in node.edges:
            to_node = self._get_node(nodes, edge.toNodeId)

            edge_type = "child"

            if node.hop == to_node.hop:
                edge_type = "sibling"

            elif node.hop < to_node.hop and not to_node.isPrimary:
                edge_type = "parent"

            edge.type = edge_type

            # print(f"- {edge.id} --> {edge.toNodeId} | {edge.type} |> {node.hop}")

    def get_zwave_nodes_json(self):
        nodes: List[Node] = self._get_zwave_nodes()

        self._update(nodes)

        items = []

        for node in nodes:
            items.append(node.to_dict())

        return items

    def get_external_nodes_json(self, path):
        with open(path[1:]) as file:
            content = file.read()

        nodes: List[Node] = []
        items = []

        if content is not None:
            data = json.loads(content)

            for item in data:
                entity = item["entity"]

                node = Node(entity)
                node.name = f"EXT {node.name}"

                nodes.append(node)

            self._update(nodes)

            for node in nodes:
                items.append(node.to_dict())

        return items

    def _update(self, nodes: List[Node]):
        hub = self._get_hub(nodes)

        if hub is None or hub.neighbors is None:
            return

        for node in nodes:
            self._update_edges(node, nodes)

        for hop in range(len(nodes)):
            if not self._update_hop(hop, nodes):
                break

        for node in nodes:
            self._update_relation_type(node, nodes)
