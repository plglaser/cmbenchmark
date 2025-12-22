"""Loss tracking system for parsers.

This module provides an extensible framework for tracking information loss
during model parsing. It supports structured loss events with categories,
reasons, and locations.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Union
from enum import Enum


class LossCategory(str, Enum):
    """Categories of loss events."""
    
    SKIPPED_SECTION = "skipped_section"
    UNSUPPORTED_ELEMENT = "unsupported_element"
    DROPPED_ATTRIBUTE = "dropped_attribute"
    DROPPED_CHILD = "dropped_child"
    INVALID_REFERENCE = "invalid_reference"


@dataclass
class LossLocation:
    """Location information for a loss event.
    
    Provides context about where in the source model the loss occurred.
    """
    
    tag: Optional[str] = None
    element_id: Optional[str] = None
    folder_type: Optional[str] = None
    attribute_name: Optional[str] = None
    child_tag: Optional[str] = None
    # Allow additional location fields
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        result = {}
        if self.tag is not None:
            result["tag"] = self.tag
        if self.element_id is not None:
            result["element_id"] = self.element_id
        if self.folder_type is not None:
            result["folder_type"] = self.folder_type
        if self.attribute_name is not None:
            result["attribute_name"] = self.attribute_name
        if self.child_tag is not None:
            result["child_tag"] = self.child_tag
        if self.extra:
            result.update(self.extra)
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LossLocation":
        """Create from dictionary."""
        extra = {k: v for k, v in data.items() 
                if k not in ("tag", "element_id", "folder_type", "attribute_name", "child_tag")}
        return cls(
            tag=data.get("tag"),
            element_id=data.get("element_id"),
            folder_type=data.get("folder_type"),
            attribute_name=data.get("attribute_name"),
            child_tag=data.get("child_tag"),
            extra=extra
        )


@dataclass
class LossEvent:
    """A single loss event with full details."""
    
    category: LossCategory
    reason: str
    loc: Optional[LossLocation] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "category": self.category.value,
            "reason": self.reason,
        }
        if self.loc is not None:
            result["loc"] = self.loc.to_dict()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LossEvent":
        """Create from dictionary."""
        loc = None
        if "loc" in data:
            loc = LossLocation.from_dict(data["loc"])
        return cls(
            category=LossCategory(data["category"]),
            reason=data["reason"],
            loc=loc
        )


@dataclass
class LossTracker:
    """Tracks loss events during parsing."""
    
    events: List[LossEvent] = field(default_factory=list)
    
    def record(self, category: LossCategory, reason: str,
               loc: Optional[LossLocation] = None) -> None:
        """Record a loss event.
        
        Args:
            category: Loss category
            reason: Human-readable reason for the loss
            loc: Location information
        """
        event = LossEvent(
            category=category,
            reason=reason,
            loc=loc
        )
        self.events.append(event)
    
    def get_summary(self) -> Dict[str, int]:
        """Compute aggregated summary counts by category.
        
        Returns:
            Dictionary mapping category names to total event counts
        """
        summary = {}
        for event in self.events:
            category = event.category.value
            summary[category] = summary.get(category, 0) + 1
        return summary
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with summary and events."""
        return {
            "summary": self.get_summary(),
            "events": [event.to_dict() for event in self.events]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LossTracker":
        """Create from dictionary."""
        tracker = cls()
        if "events" in data:
            tracker.events = [LossEvent.from_dict(e) for e in data["events"]]
        return tracker

