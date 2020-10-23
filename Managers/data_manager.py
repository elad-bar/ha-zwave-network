import json
import logging
from asyncio import sleep

from typing import List, Optional

import aiofiles as aiofiles

from Managers.configuration_manager import ConfigurationManager
from models.consts import *

from models.device_identifier import DeviceIdentifier
from models.node import Node
from models.node_relation import NodeRelation

import asyncio
import asyncws

_LOGGER = logging.getLogger(__name__)


class HAZWaveManager:
    def __init__(self, configuration: ConfigurationManager):
        self._configuration = configuration

        self._token = configuration.home_assistant_token
        self._ws_url = configuration.home_assistant_web_socket_url
        self._devices = []
        self._nodes: List[Node] = []

        self._verify = False if "wss://" in self._ws_url else None
        self._states = None
        self._domain = DOMAIN_ZWAVE

        self._ws_status = WEB_SOCKET_STATUS_DISCONNECTED

        self._ws: Optional[asyncws.Websocket] = None

        self._ws_counter = 1

    def initialize(self):
        asyncio.run(self._initialize())

    async def _initialize(self):
        is_local = self._configuration.is_local

        while True:
            try:
                if is_local:
                    await self._reload_local_data()

                else:
                    if self._ws_status == WEB_SOCKET_STATUS_DISCONNECTED:
                        await self._connect()

                    if self._ws_status == WEB_SOCKET_STATUS_CONNECTED:
                        await self._login()

                    if self._ws_status == WEB_SOCKET_STATUS_AUTHORIZED:
                        await self._reload_data()

            except Exception as ex:
                _LOGGER.error(f"Failed to refresh data due to error: {ex}")

            await sleep(30)

    async def _connect(self):
        try:
            _LOGGER.info(f"Connecting to {self._ws_url}")
            self._ws = await asyncws.connect(f'{self._ws_url}/api/websocket', ssl=True)

            self._ws_status = WEB_SOCKET_STATUS_CONNECTED

        except Exception as ex:
            self._ws_status = WEB_SOCKET_STATUS_DISCONNECTED

            _LOGGER.error(f"Failed to connect due to error: {ex}")

    async def _login(self):
        try:
            _LOGGER.info(f"Logging into {self._ws_url}")

            is_logged_in = False
            response_message = None
            ha_version = None

            login_data = {
                'type': 'auth',
                'access_token': self._token
            }

            await self._ws.send(json.dumps(login_data))

            while True:
                message = await self._ws.recv()
                if message is None:
                    break

                _LOGGER.debug(f"Login message received: {message}")

                message_json = json.loads(message)

                response_type = message_json.get("type")
                ha_version = message_json.get("ha_version", ha_version)

                if response_type == "auth_ok":
                    is_logged_in = True
                    break

            if is_logged_in:
                _LOGGER.info(f"Login completed, Home Assistant version: {ha_version}")

                self._ws_status = WEB_SOCKET_STATUS_AUTHORIZED

            else:
                _LOGGER.error(f"Failed to login due to error: {response_message}")

                self._ws_status = WEB_SOCKET_STATUS_DISCONNECTED

        except Exception as ex:
            self._ws_status = WEB_SOCKET_STATUS_DISCONNECTED

            _LOGGER.error(f"Failed to login due to error: {ex}")

    async def _reload_data(self):
        _LOGGER.info("Reloading data")

        message_mapping = {}
        data = {}

        for request_key in WS_MAIN_DETAILS:
            self._ws_counter += 1

            request_type = WS_MAIN_DETAILS.get(request_key)

            message_mapping[self._ws_counter] = request_key

            data = {
                "id": self._ws_counter,
                "type": request_type
            }

            await self._ws.send(json.dumps(data))

        while len(message_mapping.keys()) > 0:
            message = await self._ws.recv()
            if message is None:
                break

            message_json = json.loads(message)
            if self._is_valid(message_json):
                if "id" in message_json:
                    message_id = message_json.get("id", 0)
                    result = message_json.get("result")

                    data_item = message_mapping.get(message_id)
                    data[data_item] = result

                    await self._save_debug_file(data_item, result)

                    del message_mapping[message_id]

                else:
                    _LOGGER.warning(f"Unexpected message received: {message_json}")

        await self.load_devices(data)

        if self._domain == DOMAIN_OZW:
            await self._reload_ozw_data()

        await self._save_debug_file(f"Nodes", self._devices)

        self._update_nodes()

        _LOGGER.info("Data reloaded")

    async def _reload_local_data(self):
        _LOGGER.info("Loading from local debug files")

        data = {}

        for key in WS_MAIN_DETAILS.keys():
            data_item = await self._get_debug_file(key)
            data[key] = data_item

        await self.load_devices(data)

        if self._domain == DOMAIN_OZW:
            for device in self._devices:
                device_node_id = device.get("NodeID")

                device_status = await self._get_debug_file(f"OZWStatus_{device_node_id}")

                device["OZWStatus"] = device_status

        self._update_nodes()

    async def _reload_ozw_data(self):
        _LOGGER.info("Processing OZW data")
        message_mapping = {}

        for device in self._devices:
            device_controller_id = device.get("ControllerID")
            device_node_id = device.get("NodeID")
            device_instance_id = device.get("InstanceID")

            device_key = self.get_message_id(device_controller_id, device_node_id, device_instance_id)

            new_message_id = await self.load_ozw_device(device)

            if new_message_id is not None:
                message_mapping[new_message_id] = device_key

        while len(message_mapping.keys()) > 0:
            message = await self._ws.recv()
            if message is None:
                break

            message_json = json.loads(message)

            if self._is_valid(message_json):
                if "id" in message_json:
                    message_id = message_json.get("id", 0)
                    result = message_json.get("result")

                    if message_id > 0:
                        message_device_key = message_mapping[message_id]

                        for device in self._devices:
                            device_controller_id = device.get("ControllerID")
                            device_node_id = device.get("NodeID")
                            device_instance_id = device.get("InstanceID")

                            device_key = self.get_message_id(device_controller_id, device_node_id, device_instance_id)

                            if message_device_key == device_key:
                                _LOGGER.info(f"Processing OZW device {device_node_id}")

                                await self._save_debug_file(f"OZWStatus_{device_node_id}", result)

                                device["OZWStatus"] = result

                        del message_mapping[message_id]

                else:
                    _LOGGER.warning(f"Unexpected message received: {message_json}")

        _LOGGER.info("OZW data processed")

    def _update_nodes(self):
        nodes = []

        for device in self._devices:
            node = Node(device)

            nodes.append(node)

        hub = self._get_hub(nodes)

        if hub is None or hub.neighbors is None:
            _LOGGER.error("No hub found")
            return

        for node in nodes:
            self._update_edges(node, nodes)

        for hop in range(len(nodes)):
            if not self._update_hop(hop, nodes):
                break

        for node in nodes:
            self._update_relation_type(node, nodes)

        self._nodes = nodes

    @staticmethod
    def _is_valid(message):
        message_id = message.get("id", 0)
        success = message.get("success", False)
        error = message.get("error")
        error_message = f"Message #{message_id} failed due to "

        if not success:
            if error is None:
                error_message = f"{error_message} unknown reason"
            else:
                error_code = error.get("code", 0)
                error_data = error.get("message")

                error_code_details = WEB_SOCKET_ERRORS.get(error_code, "unknown error code")

                error_message = f"{error_message} {error_code_details.lower()} [#{error_code}]"

                if error_data is not None:
                    error_message = f"{error_message}, additional details: {error_data}"

            _LOGGER.error(error_message)

        return success

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

                _LOGGER.debug(f"Associate nodes W/O neighbors: {relation.id} --> {relation.toNodeId}")

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

                    _LOGGER.debug(f"Associate reverse nodes W/O neighbors: {op_relation.id} --> {op_relation.toNodeId}")

                    hub.edges.append(op_relation)
        else:
            for neighbor_id in neighbors:
                neighbor = self._get_node(nodes, neighbor_id)

                if neighbor is not None:
                    relation = NodeRelation()
                    relation.id = node.id
                    relation.toNodeId = neighbor.id

                    _LOGGER.debug(f"Associate nodes: {relation.id} --> {relation.toNodeId}")

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

                        _LOGGER.debug(f"Associate reverse nodes: {op_relation.id} --> {op_relation.toNodeId}")

                        neighbor.edges.append(op_relation)

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

            _LOGGER.debug(f"Processing node {node.id}, HOP:{node.hop}")

            for edge in node.edges:
                to_node = self._get_node(nodes, edge.toNodeId)

                _LOGGER.debug(f"Processing nested node {to_node.id}, HOP:{to_node.hop}")

                if to_node is not None and to_node.hop == -1:
                    to_node.hop = current_hop + 1

                    _LOGGER.debug(f"Changed HOP of nested node {to_node.id} to {to_node.hop}")

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

            msg = f"Update relation of node {edge.id} to node {edge.toNodeId}, Type: {edge.type}, HOP: {node.hop}"
            _LOGGER.debug(msg)

    def get_nodes(self):
        return self._nodes

    async def load_devices(self, data):
        _LOGGER.info(f"Loading devices")

        devices = data.get("Devices")
        entities = data.get("Entities")
        states = data.get("States")

        all_devices = {}

        for device in devices:
            device_id = device.get("id")
            device_identifier = self.get_device_identifier(device)

            device["Domain"] = device_identifier.domain
            device["ControllerID"] = device_identifier.controller_id
            device["NodeID"] = device_identifier.node_id
            device["InstanceID"] = device_identifier.instance_id

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

            if all_devices.get(device_identifier.domain) is None:
                all_devices[device_identifier.domain] = []

            all_devices[device_identifier.domain].append(device)

        if len(all_devices.get(DOMAIN_OZW, [])) > 0:
            self._domain = DOMAIN_OZW

        self._devices = all_devices.get(self._domain, [])

        _LOGGER.info(f"{len(self._devices)} {self._domain.upper()} devices loaded")

    @staticmethod
    def get_device_identifier(device):
        is_valid = False
        device_id = device.get("id")
        identifiers = device.get("identifiers", [])

        device_identifier = DeviceIdentifier()

        if identifiers is not None and len(identifiers) > 0:
            identifier_parts = identifiers[0]

            if identifier_parts is not None:
                if len(identifier_parts) > 1:
                    is_valid = True

                    device_identifier.domain = identifier_parts[0]
                    external_id = identifier_parts[1]

                    if device_identifier.domain == DOMAIN_OZW:
                        external_id_parts = external_id.split(".")

                        if len(external_id) > 2:
                            device_identifier.controller_id = int(external_id_parts[0])
                            device_identifier.node_id = int(external_id_parts[1])
                            device_identifier.instance_id = int(external_id_parts[2])
                        else:
                            is_valid = False
                    else:
                        device_identifier.node_id = external_id

                if len(identifier_parts) > 2:
                    device_identifier.instance_id = int(identifier_parts[2])

        if not is_valid:
            _LOGGER.warning(f"Invalid device {device_id} identifiers: {identifiers}")

        return device_identifier

    @staticmethod
    async def _save_debug_file(name, data):
        content = json.dumps(data, indent=4)

        async with aiofiles.open(f"/debug/{name.lower()}.json", mode='w') as f:
            await f.write(content)

    @staticmethod
    async def _get_debug_file(name):
        async with aiofiles.open(f"/debug/{name.lower()}.json", mode='r') as f:
            content = await f.read()

            data = json.loads(content)

            return data

    async def load_ozw_device(self, device) -> Optional[int]:
        message_id = None

        node_id = device.get("NodeID")
        instance_id = device.get("InstanceID")

        if instance_id == 1:
            self._ws_counter += 1

            message_id = self._ws_counter

            device_status = {
                "id": self._ws_counter,
                "type": "ozw/node_status",
                "ozw_instance": instance_id,
                "node_id": node_id
            }

            await self._ws.send(json.dumps(device_status))

        return message_id

    @staticmethod
    def get_message_id(controller_id, node_id, instance_id):
        return (controller_id * 1000000) + (node_id * 10000) + (instance_id * 10)
