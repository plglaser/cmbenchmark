"""UML parser handlers for different element types."""

from cmbenchmark.parser.uml.handlers.base_handler import ElementHandler
from cmbenchmark.parser.uml.handlers.model_handler import ModelHandler
from cmbenchmark.parser.uml.handlers.package_handler import PackageHandler
from cmbenchmark.parser.uml.handlers.class_handler import ClassHandler
from cmbenchmark.parser.uml.handlers.interface_handler import InterfaceHandler
from cmbenchmark.parser.uml.handlers.association_handler import AssociationHandler
from cmbenchmark.parser.uml.handlers.generalization_handler import GeneralizationHandler
from cmbenchmark.parser.uml.handlers.enumeration_handler import EnumerationHandler
from cmbenchmark.parser.uml.handlers.datatype_handler import DataTypeHandler
from cmbenchmark.parser.uml.handlers.usecase_handler import UseCaseHandler
from cmbenchmark.parser.uml.handlers.actor_handler import ActorHandler

__all__ = [
    "ElementHandler",
    "ModelHandler",
    "PackageHandler",
    "ClassHandler",
    "InterfaceHandler",
    "AssociationHandler",
    "GeneralizationHandler",
    "EnumerationHandler",
    "DataTypeHandler",
    "UseCaseHandler",
    "ActorHandler",
]
