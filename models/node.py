from typing import Optional, List

from models.node_relation import NodeRelation


class Node:
    id: Optional[int]
    name: Optional[str]
    hop: Optional[int]
    neighbors: List[int]
    isPrimary: Optional[bool]
    isFailed: Optional[bool]
    isAwake: Optional[bool]
    isReady: Optional[bool]
    isZWavePlus: Optional[bool]
    isBeaming: Optional[bool]
    isListening: Optional[bool]
    isRouting: Optional[bool]
    isSecure: Optional[bool]
    edges: List[NodeRelation]
    product: Optional[str]
    manufacturer: Optional[str]
    queryStage: Optional[str]
    lastResponseRTT: Optional[str]
    batteryLevel: Optional[str]
    version: Optional[str]
    entityCount: Optional[int]
    device: dict

    def __init__(self, device: dict):
        name = device.get("name")

        name_by_user = device.get("name_by_user")
        if name_by_user is not None:
            name = name_by_user

        node_id = device.get("NodeID")

        self.neighbors = []
        self.isPrimary = None
        self.isFailed = None
        self.isAwake = None
        self.isReady = None
        self.isZWavePlus = None
        self.isBeaming = None
        self.isListening = None
        self.isRouting = None
        self.isSecure = None
        self.product = None
        self.manufacturer = None
        self.queryStage = None
        self.lastResponseRTT = None
        self.batteryLevel = None
        self.version = None
        self.entityCount = len(device.get("Entities", []))

        if "OZWStatus" in device:
            device_status = device.get("OZWStatus")

            if device_status is not None:
                device_type = device_status.get("node_basic_string")

                self.neighbors = device_status.get("neighbors")
                self.isFailed = device_status.get("is_failed")
                self.isAwake = device_status.get("is_awake")
                self.isZWavePlus = device_status.get("is_zwave_plus")
                self.isBeaming = device_status.get("is_beaming")
                self.isSecure = device_status.get("is_securityv1")
                self.isRouting = device_status.get("is_routing")

                self.isPrimary = device_type == "Static Controller"

                self.product = device_status.get("node_product_name")
                self.manufacturer = device_status.get("node_manufacturer_name")
                self.queryStage = device_status.get("node_query_stage")
                self.version = device.get("sw_version")

                for entity in device.get("Entities", []):
                    entity_id = entity.get("entity_id")

                    if "battery_level" in entity_id:
                        state = entity.get("State", {})
                        self.batteryLevel = state.get("state")

                        break

        elif "ZWaveStatus" in device:
            device_status = device.get("ZWaveStatus")

            if device_status is not None:
                attributes = device_status.get("attributes", {})

                capabilities = attributes.get("capabilities", [])

                self.neighbors = attributes.get("neighbors")
                self.isFailed = attributes.get("is_failed")
                self.isAwake = attributes.get("is_awake")
                self.isReady = attributes.get("is_ready")
                self.isZWavePlus = attributes.get("is_zwave_plus")

                self.isPrimary = "primaryController" in capabilities
                self.isBeaming = "beaming" in capabilities
                self.isListening = "listening" in capabilities
                self.isRouting = "routing" in capabilities

                self.product = attributes.get("product_name")
                self.manufacturer = attributes.get("manufacturer_name")
                self.queryStage = attributes.get("query_stage")
                self.lastResponseRTT = attributes.get("lastResponseRTT")
                self.batteryLevel = attributes.get("battery_level")
                self.version = attributes.get("application_version")

        self.id = node_id
        self.name = name
        self.hop = 0 if self.isPrimary else -1
        self.device = device
        self.edges = []

    def __repr__(self):
        return f"{self.__dict__}"
