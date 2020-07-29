from typing import Optional, List

from models.node_relation import NodeRelation


class Node:
    id: Optional[int]
    name: Optional[str]
    hop: Optional[int]
    neighbors: List[int]
    isPrimary: Optional[bool]
    edges: List[NodeRelation]
    entity: dict

    def __init__(self, entity: dict):
        attributes = entity.get("attributes", {})
        node_id = attributes.get("node_id")
        neighbors = attributes.get("neighbors")
        name = attributes.get("friendly_name")
        capabilities = attributes.get("capabilities", [])

        is_primary = "primaryController" in capabilities

        self.id = node_id
        self.name = name
        self.hop = 0 if is_primary else -1
        self.neighbors = neighbors
        self.isPrimary = is_primary
        self.entity = entity
        self.edges = []

    def to_dict(self):
        obj = {
            "id": self.id,
            "name": self.name,
            "hop": self.hop,
            "neighbors": self.neighbors,
            "isPrimary": self.isPrimary,
            "edges": [],
            "entity": self.entity
        }
        edges = []
        for edge in self.edges:
            edges.append(edge.to_dict())

        obj["edges"] = edges

        return obj

    def __repr__(self):
        return f"{self.to_dict()}"
