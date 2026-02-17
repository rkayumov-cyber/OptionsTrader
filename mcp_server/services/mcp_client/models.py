"""Pydantic models for MCP client configuration and status."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MCPServerConfig(BaseModel):
    """Configuration for a single external MCP server."""

    name: str
    enabled: bool = True
    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    capabilities: list[str] = Field(default_factory=list)
    tool_mappings: dict[str, str] = Field(default_factory=dict)
    tool_call_wrapper: str | None = None  # e.g. "TOOL_CALL" for AV-style meta-tool servers
    param_mappings: dict[str, str] = Field(default_factory=dict)  # generic_arg -> server_arg
    tool_param_overrides: dict[str, dict[str, str]] = Field(
        default_factory=dict
    )  # tool_name -> {generic_arg -> server_arg}


class MCPServerStatus(BaseModel):
    """Runtime status of an MCP server connection."""

    id: str
    name: str
    enabled: bool
    status: str = "disconnected"  # connected, disconnected, error, connecting
    tools: list[str] = Field(default_factory=list)
    tool_count: int = 0
    error: str | None = None
    connected_at: datetime | None = None
    call_count: int = 0
    avg_response_ms: float = 0.0
    capabilities: list[str] = Field(default_factory=list)


class MCPToolCallResult(BaseModel):
    """Result from calling a tool on an MCP server."""

    server_id: str
    tool_name: str
    success: bool
    data: Any = None
    error: str | None = None
    duration_ms: float = 0.0


class MCPServersConfig(BaseModel):
    """Top-level config loaded from mcp_servers.yaml."""

    mcp_servers: dict[str, MCPServerConfig] = Field(default_factory=dict)
    fallback_priority: dict[str, list[str]] = Field(default_factory=dict)
