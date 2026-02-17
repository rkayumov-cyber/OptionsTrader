"""MCPClientManager - launches and manages external MCP server processes via stdio."""

import asyncio
import logging
import os
import time
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any

import yaml
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .models import (
    MCPServerConfig,
    MCPServersConfig,
    MCPServerStatus,
    MCPToolCallResult,
)

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "config" / "mcp_servers.yaml"


class MCPClientManager:
    """Manages connections to external MCP servers."""

    def __init__(self, config_path: Path | None = None):
        self._config_path = config_path or CONFIG_PATH
        self._config: MCPServersConfig = MCPServersConfig()
        self._sessions: dict[str, ClientSession] = {}
        self._statuses: dict[str, MCPServerStatus] = {}
        self._exit_stack = AsyncExitStack()
        self._call_counts: dict[str, int] = {}
        self._total_response_ms: dict[str, float] = {}

    def _load_config(self) -> MCPServersConfig:
        """Load MCP servers config from YAML file."""
        if not self._config_path.exists():
            logger.warning("MCP servers config not found at %s", self._config_path)
            return MCPServersConfig()

        with open(self._config_path) as f:
            raw = yaml.safe_load(f) or {}

        # Expand env vars in server env
        servers = {}
        for server_id, server_data in raw.get("mcp_servers", {}).items():
            if "env" in server_data:
                expanded_env = {}
                for k, v in server_data["env"].items():
                    if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
                        env_name = v[2:-1]
                        expanded_env[k] = os.environ.get(env_name, "")
                    else:
                        expanded_env[k] = v
                server_data["env"] = expanded_env
            servers[server_id] = MCPServerConfig(**server_data)

        return MCPServersConfig(
            mcp_servers=servers,
            fallback_priority=raw.get("fallback_priority", {}),
        )

    async def startup(self) -> None:
        """Connect to all enabled MCP servers on FastAPI startup."""
        self._config = self._load_config()
        logger.info(
            "MCP Client Manager starting with %d configured servers",
            len(self._config.mcp_servers),
        )

        tasks = []
        for server_id, server_config in self._config.mcp_servers.items():
            # Initialize status for all servers
            self._statuses[server_id] = MCPServerStatus(
                id=server_id,
                name=server_config.name,
                enabled=server_config.enabled,
                status="disconnected",
                capabilities=server_config.capabilities,
            )
            if server_config.enabled:
                tasks.append(self._connect_server(server_id, server_config))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for server_id, result in zip(
                [sid for sid, sc in self._config.mcp_servers.items() if sc.enabled],
                results,
            ):
                if isinstance(result, Exception):
                    logger.error("Failed to connect to %s: %s", server_id, result)
                    self._statuses[server_id].status = "error"
                    self._statuses[server_id].error = str(result)

    async def shutdown(self) -> None:
        """Disconnect all MCP servers on FastAPI shutdown."""
        logger.info("MCP Client Manager shutting down")
        self._sessions.clear()
        await self._exit_stack.aclose()
        for status in self._statuses.values():
            status.status = "disconnected"

    async def _connect_server(
        self, server_id: str, config: MCPServerConfig
    ) -> None:
        """Launch subprocess via stdio_client, create ClientSession, discover tools."""
        self._statuses[server_id].status = "connecting"
        logger.info("Connecting to MCP server: %s (%s)", server_id, config.name)

        server_params = StdioServerParameters(
            command=config.command,
            args=config.args,
            env={**os.environ, **config.env} if config.env else None,
        )

        # Enter the stdio_client context and keep it alive via exit_stack
        stdio_transport = await self._exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        read_stream, write_stream = stdio_transport

        session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )

        await session.initialize()

        # Discover available tools
        tools_result = await session.list_tools()
        tool_names = [t.name for t in tools_result.tools]

        self._sessions[server_id] = session
        self._call_counts[server_id] = 0
        self._total_response_ms[server_id] = 0.0

        self._statuses[server_id].status = "connected"
        self._statuses[server_id].tools = tool_names
        self._statuses[server_id].tool_count = len(tool_names)
        self._statuses[server_id].connected_at = (
            __import__("datetime").datetime.now()
        )
        self._statuses[server_id].error = None

        logger.info(
            "Connected to %s: %d tools available: %s",
            server_id,
            len(tool_names),
            tool_names,
        )

    async def call_tool(
        self, server_id: str, tool_name: str, args: dict[str, Any] | None = None
    ) -> MCPToolCallResult:
        """Call a specific tool on an MCP server."""
        if server_id not in self._sessions:
            return MCPToolCallResult(
                server_id=server_id,
                tool_name=tool_name,
                success=False,
                error=f"Server '{server_id}' not connected",
            )

        session = self._sessions[server_id]
        start = time.monotonic()

        try:
            result = await session.call_tool(tool_name, arguments=args or {})
            duration = (time.monotonic() - start) * 1000

            self._call_counts[server_id] = self._call_counts.get(server_id, 0) + 1
            self._total_response_ms[server_id] = (
                self._total_response_ms.get(server_id, 0) + duration
            )
            self._statuses[server_id].call_count = self._call_counts[server_id]
            self._statuses[server_id].avg_response_ms = (
                self._total_response_ms[server_id] / self._call_counts[server_id]
            )

            # Extract text content from MCP result
            if result.isError:
                return MCPToolCallResult(
                    server_id=server_id,
                    tool_name=tool_name,
                    success=False,
                    error=str(result.content),
                    duration_ms=duration,
                )

            # Parse the content - MCP returns list of content items
            data = None
            for content_item in result.content:
                if hasattr(content_item, "text"):
                    import json

                    try:
                        data = json.loads(content_item.text)
                    except (json.JSONDecodeError, TypeError):
                        data = content_item.text
                    break

            return MCPToolCallResult(
                server_id=server_id,
                tool_name=tool_name,
                success=True,
                data=data,
                duration_ms=duration,
            )

        except Exception as e:
            duration = (time.monotonic() - start) * 1000
            logger.error(
                "Error calling %s on %s: %s", tool_name, server_id, e
            )
            return MCPToolCallResult(
                server_id=server_id,
                tool_name=tool_name,
                success=False,
                error=str(e),
                duration_ms=duration,
            )

    async def call_tool_with_fallback(
        self,
        data_type: str,
        mapping_key: str,
        args: dict[str, Any] | None = None,
    ) -> MCPToolCallResult | None:
        """Try servers in fallback priority order for a given data type."""
        priority = self._config.fallback_priority.get(data_type, [])

        for server_id in priority:
            if server_id not in self._sessions:
                continue

            config = self._config.mcp_servers.get(server_id)
            if not config:
                continue

            tool_name = config.tool_mappings.get(mapping_key)
            if not tool_name:
                continue

            result = await self.call_tool(server_id, tool_name, args)
            if result.success:
                return result

            logger.warning(
                "Fallback %s/%s failed: %s", server_id, tool_name, result.error
            )

        return None

    def get_all_statuses(self) -> list[MCPServerStatus]:
        """Return status for all configured servers."""
        return list(self._statuses.values())

    def get_status(self, server_id: str) -> MCPServerStatus | None:
        """Return status for a single server."""
        return self._statuses.get(server_id)

    def get_tools(self, server_id: str) -> list[str]:
        """Return available tools for a server."""
        status = self._statuses.get(server_id)
        return status.tools if status else []

    async def toggle_server(self, server_id: str) -> MCPServerStatus | None:
        """Enable/disable a server. Connects/disconnects as needed."""
        if server_id not in self._statuses:
            return None

        status = self._statuses[server_id]
        config = self._config.mcp_servers.get(server_id)
        if not config:
            return None

        if status.enabled:
            # Disable - disconnect if connected
            status.enabled = False
            config.enabled = False
            if server_id in self._sessions:
                # We can't cleanly remove from exit_stack, but we can
                # remove the session reference so it won't be used
                del self._sessions[server_id]
            status.status = "disconnected"
            status.tools = []
            status.tool_count = 0
        else:
            # Enable - try to connect
            status.enabled = True
            config.enabled = True
            try:
                await self._connect_server(server_id, config)
            except Exception as e:
                status.status = "error"
                status.error = str(e)

        return status

    async def reconnect_server(self, server_id: str) -> MCPServerStatus | None:
        """Force reconnect a server."""
        if server_id not in self._statuses:
            return None

        config = self._config.mcp_servers.get(server_id)
        if not config or not config.enabled:
            return None

        # Remove existing session
        if server_id in self._sessions:
            del self._sessions[server_id]

        status = self._statuses[server_id]
        try:
            await self._connect_server(server_id, config)
        except Exception as e:
            status.status = "error"
            status.error = str(e)

        return status

    @property
    def config(self) -> MCPServersConfig:
        return self._config
