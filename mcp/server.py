"""
MCP Server Execution Engine Module.
Executes MCP tool requests against the active data repository.
"""

from mcp.registry import MCPToolRegistry

_GLOBAL_REGISTRY = MCPToolRegistry()

class MCPServer:
    @staticmethod
    def list_registered_tools():
        return list(_GLOBAL_REGISTRY.tools.keys())

    @staticmethod
    def execute_tool(tool_name, kwargs, repo, table="energymeter"):
        if "table" not in kwargs and table:
            kwargs["table"] = table
        return _GLOBAL_REGISTRY.execute_tool(tool_name, kwargs, repo, table)
