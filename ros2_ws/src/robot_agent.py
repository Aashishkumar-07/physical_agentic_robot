from langchain_core.messages import (BaseMessage,HumanMessage,SystemMessage)
from typing import Annotated, Annotated, Sequence, Any, Dict, TypedDict
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, END, add_messages
from langchain.chat_models import init_chat_model
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import ToolNode
from pydantic import create_model
from dotenv import load_dotenv
from pathlib import Path
import asyncio
import os

load_dotenv()
SYSTEM_PROMPT = Path("./system_prompt.md").read_text(encoding="utf-8")

# -----------------------------
# Helper: coercion logic
# -----------------------------
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

# -----------------------------
# JSON Schema → Pydantic
# ----------------------------- 
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

# -----------------------------
# Tool Wrapper
# -----------------------------
# JSON schema provided by MCP server converted to pydantic model for LangChain validation.
# At the time of tool call, arguments are coerced to the correct type based on the JSON schema before invoking the tool.
def create_wrapped_tool(tool, schema):
    ArgsModel = json_schema_to_pydantic(f"{tool.name}_args", schema)

    def _call(**kwargs):
        fixed_args = coerce_args(kwargs, schema)

        print(f"✅ COERCED ARGS: {fixed_args}")

        return  tool.ainvoke(fixed_args)

    return StructuredTool(
        name=tool.name,
        description=tool.description,
        coroutine=_call,
        args_schema=ArgsModel,
    )

# -----------------------------
# LangGraph State
# -----------------------------
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

# -----------------------------
# Main
# -----------------------------
async def main():
    try:
        # -----------------------------
        # MCP Client
        # -----------------------------
        mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:3001/mcp")
        client = MultiServerMCPClient({
            "nav2_mcp_server": {
                "transport": "streamable_http",
                "url": mcp_server_url,
            }
        })

        print("🔧 Fetching tools...")

        tools = await client.get_tools()
        for tool in tools:
            print(f" - {tool.name}")

        wrapped_tools = [
            create_wrapped_tool(tool, tool.args_schema)
            for tool in tools
        ]

        # -----------------------------
        # Model
        # -----------------------------
        model = init_chat_model(model="qwen3:8b", model_provider="ollama").bind_tools(tools=wrapped_tools, tool_choice="auto")
        print("✅ LLM initialized")

        # -----------------------------
        # Planner Node
        # -----------------------------
        def planner(state: AgentState):
            print("-" * 30 + "ENTERING PLANNER NODE " + "-" * 30) 
            print(f"🧠 Planner received messages: {state['messages']}")

            system_prompt = SystemMessage(content=SYSTEM_PROMPT)
            response = model.invoke([system_prompt] + state["messages"])

            print(f"🧠 Planner response: {response}")
            print("\n"+"-" * 30 + "EXITING PLANNER NODE " + "-" * 30) 

            return {"messages": [response]}

        # -----------------------------
        # Router
        # -----------------------------
        def should_continue(state: AgentState):
            print("-" * 30 + "ENTERING DECISION NODE " + "-" * 30)
            messages = state["messages"]
            last_message = messages[-1]

            print(f"🔍 Deciding should continue ?: {last_message}")
            print("last_message.tool_calls", last_message.tool_calls)

            if not last_message.tool_calls: 
                print("✅ No tool calls detected, finishing execution.")
                return END

            print("✅ Tool call detected, routing to tools.")
            return "tools"

        # -----------------------------
        # Build Graph
        # -----------------------------
        graph = StateGraph(AgentState)

        tool_node = ToolNode(tools=wrapped_tools)
        graph.add_node("planner", planner)
        graph.add_node("tools", tool_node)
        graph.add_edge("tools", "planner")
        graph.set_entry_point("planner")

        graph.add_conditional_edges(
            "planner",
            should_continue,
            {
                "tools": "tools",
                END: END
            }
        )
        app = graph.compile()

        # -----------------------------
        # Run Query
        # -----------------------------
        coversation_history = []
        user_input = input("Enter your query for the robot: ")

        print(f"\n👤 User: {user_input}\n")
        while user_input != "exit":
            coversation_history.append(HumanMessage(content=user_input))
            result = await app.ainvoke({"messages": coversation_history})

            print(f" results[`messages`]: {result['messages']}")
            print(f"\n🤖 Final Answer:\n{result['messages'][-1].content}")

            coversation_history  = result["messages"]
            user_input = input("Enter your query for the robot (type 'exit' to quit): ")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        print("\n✅ Done")

if __name__ == "__main__":
    asyncio.run(main())