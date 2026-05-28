from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import StructuredTool
from typing import List, Optional, Dict, Any
from pydantic import create_model
import os

# ===============================
# Helper: coercion logic
# ===============================
def coerce_value(value: Any, schema: Dict[str, Any]) -> Any:
    if value is None:
        return value

    schema_type = schema.get("type")

    if schema_type == "number":
        if isinstance(value, str):
            return float(value)

    if schema_type == "integer":
        if isinstance(value, str):
            return int(float(value))
        
    return value

def coerce_args(args: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    if not schema or "properties" not in schema:
        return args

    properties = schema["properties"]
    coerced = {}

    for key, value in args.items():
        if key not in properties:
            coerced[key] = value
            continue

        prop_schema = properties[key]

        if isinstance(value, dict) and prop_schema.get("type") == "object":
            coerced[key] = coerce_args(value, prop_schema)
        else:
            coerced[key] = coerce_value(value, prop_schema)

    return coerced

# ===============================
# JSON Schema → Pydantic
# =============================== 
def json_schema_to_pydantic(name: str, schema: Dict[str, Any]):
    fields = {}

    for key, prop in schema.get("properties", {}).items():
        field_type = Any

        if prop.get("type") == "number":
            field_type = float
        elif prop.get("type") == "integer":
            field_type = int
        elif prop.get("type") == "string":
            field_type = str
        elif prop.get("type") == "boolean":
            field_type = bool

        default = ... if key in schema.get("required", []) else None
        fields[key] = (field_type, default)

    return create_model(name, **fields)

# ===============================
# Tool Wrapper
# ===============================
"""
MCP tools expose input schemas as JSON Schema, but langchain-mcp-adapters
creates Pydantic V2 models from the JSON Schema and validates tool
arguments before invoking the tool. Pydantic V2 does not coerce types by
default, so LLM-generated args like "1.57" (str) fail validation against
a `number` field.

This wrapper:
1. Converts JSON Schema → Pydantic model so LangChain knows the arg structure
2. Coerce LLM-generated arguments into schema-compatible types
   before Pydantic validation runs
3. Safely invokes the underlying MCP tool with the coerced args
"""
def create_wrapped_tool(tool, schema):
    ArgsModel = json_schema_to_pydantic(f"{tool.name}_args", schema)

    async def _call(**kwargs):
        fixed_args = coerce_args(kwargs, schema)

        print(f"✅ COERCED ARGS: {fixed_args}")

        return await tool.ainvoke(fixed_args)

    return StructuredTool(
        name=tool.name,
        description=tool.description,
        coroutine=_call,
        args_schema=ArgsModel,
    )

class MCPToolRegistry:
    def __init__(self):
        self._nav2_tools: List = []
        self._faiss_tools: List = []
        self._initialized = False

    async def fetch_tools(self):
        if self._initialized:
            return

        # ===============================
        # MCP Client
        # ===============================
        mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:3001/mcp")
        client = MultiServerMCPClient({
            "nav2_mcp_server": {
                "transport": "streamable_http",
                "url": mcp_server_url,
            }
        })

        # ===============================
        # Fetch Tools
        # ===============================
        print("🔧 Fetching tools...")
        tools = await client.get_tools()
        for tool in tools:
            print(f" - {tool.name}")
            wrapped_tool = create_wrapped_tool(tool, tool.args_schema)

            if tool.name == "faiss_search":
                self._faiss_tools.append(wrapped_tool)
            else:
                self._nav2_tools.append(wrapped_tool)

        self._initialized = True

    # ===============================
    # Getter
    # ===============================
    def _ensure_initialized(self):
        if not self._initialized:
            raise RuntimeError("MCPToolRegistry not initialized. Call fetch_tools() first.")
        
    def get_nav2_tools(self) -> List:
        self._ensure_initialized()
        return self._nav2_tools

    def get_faiss_tools(self) -> List:
        self._ensure_initialized()
        return self._faiss_tools

    def get_all_tools(self) -> List:
        self._ensure_initialized()
        return self._nav2_tools + self._faiss_tools
