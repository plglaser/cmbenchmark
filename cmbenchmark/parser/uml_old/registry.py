"""Registry initialization for UML handlers."""

from .handlers.base import HandlerRegistry
from .handlers.nodes.classlike import ClasslikeHandler
from .handlers.nodes.usecase import UseCaseHandler
from .handlers.nodes.enumeration import EnumerationHandler
from .handlers.edges.association import AssociationHandler
from .handlers.edges.generalization import GeneralizationHandler
from .handlers.edges.include import IncludeHandler
from .handlers.edges.extend import ExtendHandler


def create_registry() -> HandlerRegistry:
    """Create and populate a handler registry with all UML handlers."""
    registry = HandlerRegistry()
    
    # Register node handlers
    registry.register_node(ClasslikeHandler())
    registry.register_node(UseCaseHandler())
    registry.register_node(EnumerationHandler())
    
    # Register edge handlers
    registry.register_edge(AssociationHandler())
    registry.register_edge(GeneralizationHandler())
    registry.register_edge(IncludeHandler())
    registry.register_edge(ExtendHandler())
    
    return registry

