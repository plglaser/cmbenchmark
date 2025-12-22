"""Base handler protocols and registry for UML parsing."""

from typing import Protocol, Optional, Dict, Tuple
from cmbenchmark.types.ir import Node, Edge
from ..context import ElementView, ParseContext


class NodeHandler(Protocol):
    """Protocol for node handlers."""
    
    metaclasses: Tuple[str, ...]
    
    def build(self, v: ElementView, ctx: ParseContext) -> Optional[Node]:
        """Build a Node from an ElementView."""
        ...


class EdgeHandler(Protocol):
    """Protocol for edge handlers."""
    
    metaclasses: Tuple[str, ...]
    
    def build(self, v: ElementView, ctx: ParseContext) -> Optional[Edge]:
        """Build an Edge from an ElementView."""
        ...


class HandlerRegistry:
    """Registry for node and edge handlers."""
    
    def __init__(self):
        """Initialize empty registry."""
        self._node_handlers: Dict[str, NodeHandler] = {}
        self._edge_handlers: Dict[str, EdgeHandler] = {}
    
    def register_node(self, handler: NodeHandler) -> None:
        """Register a node handler for its metaclasses."""
        for metaclass in handler.metaclasses:
            self._node_handlers[metaclass] = handler
    
    def register_edge(self, handler: EdgeHandler) -> None:
        """Register an edge handler for its metaclasses."""
        for metaclass in handler.metaclasses:
            self._edge_handlers[metaclass] = handler
    
    def get_node_handler(self, metaclass: str) -> Optional[NodeHandler]:
        """Get node handler for a metaclass."""
        return self._node_handlers.get(metaclass)
    
    def get_edge_handler(self, metaclass: str) -> Optional[EdgeHandler]:
        """Get edge handler for a metaclass."""
        return self._edge_handlers.get(metaclass)

