"""Builder functions for constructing nodes and edges from index."""

from typing import List
from cmbenchmark.types.ir import Node, Edge
from .context import ParseContext
from .handlers.base import HandlerRegistry


def build_nodes(ctx: ParseContext, registry: HandlerRegistry) -> List[Node]:
    """
    Build nodes from the index using registered handlers.
    
    Updates ctx.id_to_name as nodes are built.
    Adds warnings for unhandled metaclasses.
    """
    nodes: List[Node] = []
    
    for elem_id, v in ctx.index.items():
        handler = registry.get_node_handler(v.metaclass)
        
        if handler:
            node = handler.build(v, ctx)
            if node:
                nodes.append(node)
                # Update id_to_name for type resolution
                if v.name:
                    ctx.id_to_name[elem_id] = v.name
        else:
            # Unhandled metaclass - add warning
            ctx.warnings.append(
                f"Unhandled node metaclass {v.metaclass} id={v.id} name={v.name}"
            )
    
    return nodes


def build_edges(ctx: ParseContext, registry: HandlerRegistry) -> List[Edge]:
    """
    Build edges from the index using registered handlers.
    
    Adds warnings for unhandled metaclasses.
    """
    edges: List[Edge] = []
    
    for elem_id, v in ctx.index.items():
        handler = registry.get_edge_handler(v.metaclass)
        
        if handler:
            edge = handler.build(v, ctx)
            if edge:
                edges.append(edge)
        else:
            # Only warn if this looks like an edge metaclass
            # Skip known non-edge tags
            if v.metaclass not in (
                "Package", "Extension", "eAnnotations", "details",
                "ownedAttribute", "ownedLiteral", "ownedEnd",
                "lowerValue", "upperValue", "type", "importedPackage",
                "Class", "Component", "Actor", "UseCase", "Enumeration"
            ):
                ctx.warnings.append(
                    f"Unhandled edge metaclass {v.metaclass} id={v.id} name={v.name}"
                )
    
    return edges

