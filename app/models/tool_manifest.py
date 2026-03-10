from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class ToolType(str, Enum):
    system = "system"
    external_connector = "external_connector"
    agent_created = "agent_created"


class PricingModel(str, Enum):
    per_call = "per_call"
    per_second = "per_second"
    subscription = "subscription"


class Visibility(str, Enum):
    public = "public"
    private = "private"
    marketplace = "marketplace"


class ResourceSpec(BaseModel):
    cpu_cores: float = Field(gt=0, le=16)
    memory_mb: int = Field(gt=16, le=65536)
    disk_mb: int = Field(gt=16, le=262144)
    timeout_seconds: int = Field(gt=0, le=3600)


class ExternalDependency(BaseModel):
    type: str
    name: str
    service_id: str


class ToolManifest(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=2)
    description: str = Field(min_length=5)
    version: str
    creator_agent_id: str = Field(min_length=2)
    entrypoint: str = Field(min_length=1)
    type: ToolType
    tags: list[str] = Field(default_factory=list)
    inputs_schema: dict[str, Any] = Field(default_factory=dict)
    outputs_schema: dict[str, Any] = Field(default_factory=dict)
    resources: ResourceSpec
    cost_core_energy: float = Field(ge=0)
    pricing_model: PricingModel
    visibility: Visibility = Visibility.private
    allowed_callers: list[str] = Field(default_factory=list)
    external_dependencies: list[ExternalDependency] = Field(default_factory=list)
    secure_env_vars: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("version")
    @classmethod
    def validate_semver(cls, value: str) -> str:
        parts = value.split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise ValueError("version must use semver 'x.y.z'")
        return value

    @field_validator("inputs_schema", "outputs_schema")
    @classmethod
    def validate_json_schema_root(cls, value: dict[str, Any]) -> dict[str, Any]:
        if value and "type" not in value:
            raise ValueError("schema must include root 'type'")
        return value
