from typing import Optional


class NodeRelation:
    id: Optional[int]
    toNodeId: Optional[int]
    type: Optional[str]

    def __init__(self):
        self.id = None
        self.toNodeId = None
        self.type = None

    def to_dict(self):
        obj = {
            "id": self.id,
            "toNodeId": self.toNodeId,
            "type": self.type
        }

        return obj

    def __repr__(self):
        return f"{self.to_dict()}"
