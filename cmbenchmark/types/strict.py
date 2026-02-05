"""Strict Pydantic base model with forbidden extra fields."""

from pydantic import BaseModel, ConfigDict


class StrictBaseModel(BaseModel):
    """Base model that rejects unknown fields for strict profile validation."""

    model_config = ConfigDict(extra="forbid")
