"""UML parser handlers for different element types."""

from cmbenchmark.parser.uml.handlers.base_handler import ElementHandler
from cmbenchmark.parser.uml.handlers.model_handler import ModelHandler
from cmbenchmark.parser.uml.handlers.package_handler import PackageHandler
from cmbenchmark.parser.uml.handlers.class_handler import ClassHandler
from cmbenchmark.parser.uml.handlers.interface_handler import InterfaceHandler
from cmbenchmark.parser.uml.handlers.association_handler import AssociationHandler
from cmbenchmark.parser.uml.handlers.generalization_handler import GeneralizationHandler
from cmbenchmark.parser.uml.handlers.interface_realization_handler import InterfaceRealizationHandler
from cmbenchmark.parser.uml.handlers.dependency_handler import DependencyHandler
from cmbenchmark.parser.uml.handlers.enumeration_handler import EnumerationHandler
from cmbenchmark.parser.uml.handlers.datatype_handler import DataTypeHandler
from cmbenchmark.parser.uml.handlers.component_handler import ComponentHandler
from cmbenchmark.parser.uml.handlers.usecase_handler import UseCaseHandler
from cmbenchmark.parser.uml.handlers.include_handler import IncludeHandler
from cmbenchmark.parser.uml.handlers.extend_handler import ExtendHandler
from cmbenchmark.parser.uml.handlers.actor_handler import ActorHandler
from cmbenchmark.parser.uml.handlers.simple_node_handler import SimpleNodeHandler
from cmbenchmark.parser.uml.handlers.association_class_handler import AssociationClassHandler
from cmbenchmark.parser.uml.handlers.information_flow_handler import InformationFlowHandler
from cmbenchmark.parser.uml.handlers.directed_edge_handler import DirectedEdgeHandler

__all__ = [
    "ElementHandler",
    "ModelHandler",
    "PackageHandler",
    "ClassHandler",
    "InterfaceHandler",
    "AssociationHandler",
    "GeneralizationHandler",
    "InterfaceRealizationHandler",
    "DependencyHandler",
    "EnumerationHandler",
    "DataTypeHandler",
    "ComponentHandler",
    "UseCaseHandler",
    "IncludeHandler",
    "ExtendHandler",
    "ActorHandler",
    "SimpleNodeHandler",
    "AssociationClassHandler",
    "InformationFlowHandler",
    "DirectedEdgeHandler",
]
