from typing import Optional


class DeviceIdentifier:
    domain: Optional[str]
    node_id: Optional[str]
    instance_id: Optional[int]
    controller_id: Optional[int]

    def __init__(self):
        self.domain = None
        self.node_id = None
        self.instance_id = 1
        self.controller_id = 1

    def __repr__(self):
        return f"{self.__dict__}"
