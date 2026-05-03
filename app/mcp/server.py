from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from pydantic import BaseModel

from app.config import USE_MCP
from app.mcp.schemas import MCPTool
from app.mcp.tools import build_default_tools

logger = logging.getLogger(__name__)


def _model_validate(model_cls: type[BaseModel], payload: Any) -> BaseModel:
    if hasattr(model_cls, "model_validate"):
        return model_cls.model_validate(payload)
    return model_cls.parse_obj(payload)


def _model_dump(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


class MCPExecutionError(RuntimeError):
    pass


class MCPServer:
    def __init__(self, use_mcp: bool = USE_MCP) -> None:
        self.use_mcp = use_mcp
        self._tools: dict[str, MCPTool] = {}

    def register_tool(self, tool: MCPTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered.")
        self._tools[tool.name] = tool

    def register_tools(self, tools: list[MCPTool]) -> None:
        for tool in tools:
            self.register_tool(tool)

    def execute_tool(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        tool = self._tools.get(name)
        if not tool:
            raise MCPExecutionError(f"Tool '{name}' is not registered.")

        input_payload = _model_validate(tool.input_schema, payload)
        logger.info("MCP tool call started: %s", name)

        if not self.use_mcp:
            return self._execute_fallback(tool, input_payload, reason="MCP is disabled by USE_MCP flag.")

        try:
            output_payload = tool.handler(input_payload)
            validated_output = self._validate_output(tool, output_payload)
            logger.info("MCP tool call completed: %s", name)
            return validated_output
        except Exception as exc:
            logger.exception("MCP tool call failed: %s", name)
            return self._execute_fallback(tool, input_payload, reason=f"MCP execution failed: {exc}")

    def _validate_output(self, tool: MCPTool, output_payload: BaseModel | dict[str, Any]) -> dict[str, Any]:
        data = _model_dump(output_payload) if isinstance(output_payload, BaseModel) else output_payload
        validated = _model_validate(tool.output_schema, data)
        return _model_dump(validated)

    def _execute_fallback(self, tool: MCPTool, payload: BaseModel, reason: str) -> dict[str, Any]:
        if tool.fallback_handler is None:
            raise MCPExecutionError(f"No fallback handler configured for tool '{tool.name}'.")

        logger.warning("MCP fallback triggered for %s: %s", tool.name, reason)
        try:
            fallback_output = tool.fallback_handler(payload)
            validated_output = self._validate_output(tool, fallback_output)
            logger.info("MCP fallback completed: %s", tool.name)
            return validated_output
        except Exception as exc:
            logger.exception("MCP fallback failed: %s", tool.name)
            raise MCPExecutionError(f"Fallback failed for tool '{tool.name}': {exc}") from exc


@lru_cache(maxsize=1)
def get_mcp_server() -> MCPServer:
    server = MCPServer(use_mcp=USE_MCP)
    server.register_tools(build_default_tools())
    return server
