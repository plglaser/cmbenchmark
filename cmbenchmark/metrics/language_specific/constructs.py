"""Construct-related metrics for UML models."""

from typing import List, Dict, Any
from collections import defaultdict
import statistics
from cmbenchmark.types.ir import IR, Node, Edge


def compute_construct_metrics(ir_models: List[IR]) -> Dict[str, Any]:
    """
    Compute construct-related metrics for UML models.

    Args:
        ir_models: List of IR models with language="UML"

    Returns:
        Dictionary with construct-related metrics organized by category
    """
    if not ir_models:
        return {}

    # Aggregate data across all models
    all_classes: List[Node] = []
    all_edges: List[Edge] = []
    
    for ir in ir_models:
        classes = [node for node in ir.nodes if node.type == "Class"]
        all_classes.extend(classes)
        all_edges.extend(ir.edges)

    # Compute per-model statistics (even if no classes, we still want per-model stats)
    per_model_metrics = _compute_per_model_statistics(ir_models)

    if not all_classes:
        return {
            "classes": {},
            "attributes": {},
            "relationships": {},
            "inheritance": {},
            "per_model": per_model_metrics,
        }

    # Build class lookup for inheritance analysis
    class_by_id = {cls.id: cls for cls in all_classes}
    
    # Class metrics
    class_metrics = _compute_class_metrics(all_classes)
    
    # Attribute metrics
    attribute_metrics = _compute_attribute_metrics(all_classes)
    
    # Relationship metrics
    relationship_metrics = _compute_relationship_metrics(all_edges, class_by_id)
    
    # Inheritance metrics
    inheritance_metrics = _compute_inheritance_metrics(all_classes, all_edges, class_by_id)

    return {
        "classes": class_metrics,
        "attributes": attribute_metrics,
        "relationships": relationship_metrics,
        "inheritance": inheritance_metrics,
        "per_model": per_model_metrics,
    }


def _compute_class_metrics(classes: List[Node]) -> Dict[str, Any]:
    """Compute class-related metrics."""
    total_classes = len(classes)
    
    if total_classes == 0:
        return {
            "total": 0,
            "abstract": 0,
            "concrete": 0,
            "with_attributes": 0,
            "without_attributes": 0,
            "avg_attributes_per_class": 0.0,
        }

    abstract_classes = sum(
        1 for cls in classes 
        if cls.data.get("isAbstract", False)
    )
    concrete_classes = total_classes - abstract_classes

    classes_with_attrs = sum(
        1 for cls in classes 
        if cls.data.get("attributes") and len(cls.data["attributes"]) > 0
    )
    classes_without_attrs = total_classes - classes_with_attrs

    total_attributes = sum(
        len(cls.data.get("attributes", [])) 
        for cls in classes
    )
    avg_attributes = total_attributes / total_classes if total_classes > 0 else 0.0

    return {
        "total": total_classes,
        "abstract": abstract_classes,
        "concrete": concrete_classes,
        "with_attributes": classes_with_attrs,
        "without_attributes": classes_without_attrs,
        "avg_attributes_per_class": round(avg_attributes, 2),
    }


def _compute_attribute_metrics(classes: List[Node]) -> Dict[str, Any]:
    """Compute attribute-related metrics."""
    all_attributes = []
    for cls in classes:
        attrs = cls.data.get("attributes", [])
        all_attributes.extend(attrs)

    if not all_attributes:
        return {
            "total": 0,
            "by_visibility": {},
            "static": 0,
            "derived": 0,
            "read_only": 0,
            "with_default_value": 0,
        }

    # Visibility distribution
    visibility_counts = defaultdict(int)
    static_count = 0
    derived_count = 0
    read_only_count = 0
    with_default_count = 0

    for attr in all_attributes:
        visibility = attr.get("visibility", "public")
        visibility_counts[visibility] += 1

        if attr.get("isStatic", False):
            static_count += 1
        if attr.get("isDerived", False):
            derived_count += 1
        if attr.get("isReadOnly", False):
            read_only_count += 1
        if "default" in attr:
            with_default_count += 1

    return {
        "total": len(all_attributes),
        "by_visibility": dict(visibility_counts),
        "static": static_count,
        "derived": derived_count,
        "read_only": read_only_count,
        "with_default_value": with_default_count,
    }


def _compute_relationship_metrics(edges: List[Edge], class_by_id: Dict[str, Node]) -> Dict[str, Any]:
    """Compute relationship-related metrics."""
    associations = [e for e in edges if e.type == "Association"]
    compositions = [e for e in edges if e.type == "Composition"]
    aggregations = [e for e in edges if e.type == "Aggregation"]
    generalizations = [e for e in edges if e.type == "Generalization"]

    total_relationships = len(associations) + len(compositions) + len(aggregations) + len(generalizations)

    # Count relationships per class
    relationship_counts = defaultdict(int)
    for edge in edges:
        if edge.type in ("Association", "Composition", "Aggregation", "Generalization"):
            if edge.sourceId in class_by_id:
                relationship_counts[edge.sourceId] += 1
            if edge.targetId in class_by_id:
                relationship_counts[edge.targetId] += 1

    avg_relationships = (
        sum(relationship_counts.values()) / len(class_by_id) 
        if class_by_id and relationship_counts 
        else 0.0
    )

    return {
        "total": total_relationships,
        "associations": len(associations),
        "compositions": len(compositions),
        "aggregations": len(aggregations),
        "generalizations": len(generalizations),
        "avg_per_class": round(avg_relationships, 2),
    }


def _compute_inheritance_metrics(
    classes: List[Node], 
    edges: List[Edge], 
    class_by_id: Dict[str, Node]
) -> Dict[str, Any]:
    """Compute inheritance-related metrics."""
    generalizations = [e for e in edges if e.type == "Generalization"]
    
    if not generalizations:
        return {
            "total_generalizations": 0,
            "root_classes": len(classes),
            "leaf_classes": 0,
            "max_depth": 0,
            "avg_depth": 0.0,
        }

    # Build parent-child relationships
    children_by_parent = defaultdict(list)
    parent_by_child = {}
    
    for gen in generalizations:
        child_id = gen.sourceId
        parent_id = gen.targetId
        if child_id in class_by_id and parent_id in class_by_id:
            children_by_parent[parent_id].append(child_id)
            parent_by_child[child_id] = parent_id

    # Find root classes (no parent)
    root_classes = [
        cls.id for cls in classes 
        if cls.id not in parent_by_child
    ]

    # Find leaf classes (no children)
    leaf_classes = [
        cls.id for cls in classes 
        if cls.id not in children_by_parent
    ]

    # Compute inheritance depth for each class
    def compute_depth(class_id: str, visited: set) -> int:
        """Compute inheritance depth recursively."""
        if class_id in visited:
            return 0  # Cycle detected
        if class_id not in parent_by_child:
            return 0
        
        visited.add(class_id)
        parent_id = parent_by_child[class_id]
        return 1 + compute_depth(parent_id, visited)

    depths = []
    for cls in classes:
        depth = compute_depth(cls.id, set())
        depths.append(depth)

    max_depth = max(depths) if depths else 0
    avg_depth = sum(depths) / len(depths) if depths else 0.0

    return {
        "total_generalizations": len(generalizations),
        "root_classes": len(root_classes),
        "leaf_classes": len(leaf_classes),
        "max_depth": max_depth,
        "avg_depth": round(avg_depth, 2),
    }


def _compute_per_model_statistics(ir_models: List[IR]) -> Dict[str, Any]:
    """Compute per-model statistics (min/max/avg/median) across models."""
    if not ir_models:
        return {}

    # Collect per-model metrics
    per_model_classes = []
    per_model_attributes = []
    per_model_associations = []
    per_model_compositions = []
    per_model_aggregations = []
    per_model_generalizations = []
    per_model_abstract_classes = []
    per_model_concrete_classes = []

    for ir in ir_models:
        classes = [node for node in ir.nodes if node.type == "Class"]
        class_by_id = {cls.id: cls for cls in classes}
        
        # Count classes
        num_classes = len(classes)
        per_model_classes.append(num_classes)
        
        # Count abstract/concrete
        num_abstract = sum(1 for cls in classes if cls.data.get("isAbstract", False))
        num_concrete = num_classes - num_abstract
        per_model_abstract_classes.append(num_abstract)
        per_model_concrete_classes.append(num_concrete)
        
        # Count attributes
        total_attrs = sum(len(cls.data.get("attributes", [])) for cls in classes)
        per_model_attributes.append(total_attrs)
        
        # Count relationships by type
        associations = [e for e in ir.edges if e.type == "Association"]
        compositions = [e for e in ir.edges if e.type == "Composition"]
        aggregations = [e for e in ir.edges if e.type == "Aggregation"]
        generalizations = [e for e in ir.edges if e.type == "Generalization"]
        
        per_model_associations.append(len(associations))
        per_model_compositions.append(len(compositions))
        per_model_aggregations.append(len(aggregations))
        per_model_generalizations.append(len(generalizations))

    def compute_stats(values: List[int]) -> Dict[str, Any]:
        """Compute min, max, avg, median statistics."""
        if not values:
            return {
                "min": 0,
                "max": 0,
                "avg": 0.0,
                "median": 0.0,
            }
        
        return {
            "min": min(values),
            "max": max(values),
            "avg": round(sum(values) / len(values), 2),
            "median": round(statistics.median(values), 2),
        }

    return {
        "classes": compute_stats(per_model_classes),
        "abstract_classes": compute_stats(per_model_abstract_classes),
        "concrete_classes": compute_stats(per_model_concrete_classes),
        "attributes": compute_stats(per_model_attributes),
        "associations": compute_stats(per_model_associations),
        "compositions": compute_stats(per_model_compositions),
        "aggregations": compute_stats(per_model_aggregations),
        "generalizations": compute_stats(per_model_generalizations),
    }

