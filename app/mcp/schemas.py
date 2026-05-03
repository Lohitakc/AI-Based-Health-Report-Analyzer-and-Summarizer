from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, TypeAlias

from pydantic import BaseModel, Field


ToolHandler: TypeAlias = Callable[[BaseModel], BaseModel | dict[str, Any]]


@dataclass(frozen=True)
class MCPTool:
    name: str
    description: str
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]
    handler: ToolHandler
    fallback_handler: ToolHandler | None = None


class RetrieveContextInput(BaseModel):
    parameter_name: str = Field(..., description="Lab parameter name")
    top_k: int = Field(default=3, ge=1, le=10)
    query: str | None = Field(default=None, description="Optional explicit retrieval query")


class RetrieveContextOutput(BaseModel):
    top_k_chunks: list[str] = Field(default_factory=list)


class ResolveRangeInput(BaseModel):
    parameter_name: str = Field(..., description="Lab parameter name")


class RangeResult(BaseModel):
    minimum: float
    maximum: float
    unit: str = ""
    source_name: str = "Standard medical reference"
    source_url: str = ""


class ResolveRangeOutput(BaseModel):
    range: RangeResult | None = None


class ClassifyValueInput(BaseModel):
    value: float
    minimum: float
    maximum: float


class ClassifyValueOutput(BaseModel):
    status: str


class GenerateTextInput(BaseModel):
    system_prompt: str
    user_prompt: str
    fallback_text: str


class GenerateTextOutput(BaseModel):
    summary: str
