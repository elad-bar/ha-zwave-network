import json
import logging
import os

from typing import List, Optional

from models.consts import *

from models.node import Node
from models.node_relation import NodeRelation
import asyncio
import asyncws

_LOGGER = logging.getLogger(__name__)


class HAZWaveManager:
    token: str
    ws_url: str
    ssl_key: Optional[str]
    ssl_certificate: Optional[str]
    is_ssl: bool
    is_ready: bool
    devices: []

    def __init__(self):
        url = os.environ.get('HA_URL')
        self.token = os.environ.get('HA_TOKEN')
        self.ssl_key = os.environ.get('SSL_KEY')
        self.ssl_certificate = os.environ.get('SSL_CERTIFICATE')
        self.ws_url = url.replace("http", "ws")
        self.devices = []

        self._ws_messages_sent = 1
        self._loop = asyncio.get_event_loop()
        self._verify = False if "wss://" in url else None
        self._states = None
        self._domain = DOMAIN_ZWAVE

        if self.ssl_key == "":
            self.ssl_key = None

        if self.ssl_certificate == "":
            self.ssl_certificate = None

        self.is_ssl = self.ssl_key is not None and self.ssl_certificate is not None

        self.is_ready = True

        if url is None:
            _LOGGER.fatal("Environment variable HA_URL is empty, cannot initialize server")
            self.is_ready = False
            return

        if self.token is None:
            _LOGGER.fatal("Environment variable HA_URL is empty, cannot initialize server")
            self.is_ready = False
            return

        _LOGGER.info(f"Initializing server {SERVER_BIND}:{SERVER_PORT}, SSL: {self.is_ssl}")

    def load_data(self):
        self._loop.run_until_complete(self._async_load_data())

    def get_states(self):
        try:
            return self._states

        except Exception as ex:
            _LOGGER.error(f"Failed to retrieve states from HA, error: {ex}")

            return None

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

    def _get_nodes(self):
        result: List[Node] = []

        for device in self.devices:
            node = Node(device)

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

    def get_nodes(self):
        nodes: List[Node] = self._get_nodes()

        self._update(nodes)

        items = []

        for node in nodes:
            items.append(node.__dict__)

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

    @staticmethod
    def get_ws_requests():
        requests = {
            1: "config/device_registry/list",
            2: "config/entity_registry/list",
            3: "get_states"
        }

        return requests

    async def _async_load_data(self):
        """Simple WebSocket client for Home Assistant."""
        ws = await asyncws.connect(f'{self.ws_url}/api/websocket', ssl=True)

        login_data = {
            'type': 'auth',
             'access_token': self.token
        }

        await ws.send(json.dumps(login_data))

        requests = self.get_ws_requests()
        messages = []

        for request_key in requests:
            messages.append(request_key)

            data = {
                "id": request_key,
                "type": requests.get(request_key)
            }

            await ws.send(json.dumps(data))

        entities = []
        states = []
        devices = []

        while len(messages) > 0:
            message = await ws.recv()
            if message is None:
                break

            message_json = json.loads(message)

            if "id" in message_json:
                message_id = message_json.get("id", 0)
                result = message_json.get("result")

                if message_id == 1:
                    devices = result
                elif message_id == 2:
                    entities = result
                elif message_id == 3:
                    states = result

                messages.remove(message_id)

        self.load_devices(devices, entities, states)

        if self._domain == DOMAIN_OZW:
            for device in self.devices:
                new_message_id = await self.load_ozw_device(ws, device)

                if new_message_id is not None:
                    messages.append(new_message_id)

            while len(messages) > 0:
                message = await ws.recv()
                if message is None:
                    break

                message_json = json.loads(message)

                if "id" in message_json:
                    message_id = message_json.get("id", 0)
                    result = message_json.get("result")

                    if message_id > 0:
                        for device in self.devices:
                            device_controller_id = device.get("ControllerID")
                            device_node_id = device.get("NodeID")
                            device_instance_id = device.get("InstanceID")

                            device_key = self.get_message_id(device_controller_id, device_node_id, device_instance_id)

                            if message_id == device_key:
                                device["OZWStatus"] = result

                    messages.remove(message_id)

        await ws.close()

    @staticmethod
    def get_message_id(controller_id, node_id, instance_id):
        return (controller_id * 1000) + (node_id * 100) + (instance_id * 10)

    def load_devices(self, devices, entities, states):
        filtered_devices = []

        for device in devices:
            identifier = device.get("identifiers")[0]
            domain = identifier[0]

            if domain == DOMAIN_OZW:
                self._domain = DOMAIN_OZW

                break

        for device in devices:
            device_id = device.get("id")
            identifier = device.get("identifiers")[0]
            domain = identifier[0]
            external_id = identifier[1]

            device["Domain"] = domain

            if domain == self._domain:
                controller_id = 1
                node_id = external_id
                instance_id = 1

                if domain == DOMAIN_ZWAVE:
                    if len(identifier) > 2:
                        instance_id = identifier[2]

                elif domain == DOMAIN_OZW:
                    external_id_parts = external_id.split(".")
                    controller_id = int(external_id_parts[0])
                    node_id = int(external_id_parts[1])
                    instance_id = int(external_id_parts[2])

                device["ControllerID"] = controller_id
                device["NodeID"] = node_id
                device["InstanceID"] = instance_id

                for entity in entities:
                    entity_device_id = entity.get("device_id")

                    if device_id == entity_device_id:
                        entity_id = entity.get("entity_id")

                        for state in states:
                            state_entity_id = state.get("entity_id")

                            if state_entity_id == entity_id:
                                entity["State"] = state

                                if f"{DOMAIN_ZWAVE}." in state_entity_id:
                                    device["ZWaveStatus"] = state

                        if "Entities" not in device:
                            device["Entities"] = []

                        device["Entities"].append(entity)

                filtered_devices.append(device)

        self.devices = filtered_devices

    async def load_ozw_device(self, ws, device) -> Optional[int]:
        message_id = None

        controller_id = device.get("ControllerID")
        node_id = device.get("NodeID")
        instance_id = device.get("InstanceID")

        if instance_id == 1:
            message_id = self.get_message_id(controller_id, node_id, instance_id)

            device_status = {
                "id": message_id,
                "type": "ozw/node_status",
                "ozw_instance": instance_id,
                "node_id": node_id
            }

            await ws.send(json.dumps(device_status))

        return message_id
