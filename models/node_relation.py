from typing import Optional


class NodeRelation:

    id: Optional[int]
    toNodeId: Optional[int]
    type: Optional[str]

    def __init__(self):
        self.id = None
        self.toNodeId = None
        self.type = None

    def __repr__(self):
        return f"{self.__dict__}"
