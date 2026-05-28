from ..dispatcher.subgraph_dispatcher_tool import subgraph_dispatch, SubgraphName
from langchain_core.messages import (HumanMessage,SystemMessage, ToolMessage)
from ..registry.model_registry import AgentRegistry, ModelRegistry
from ..registry.mcp_tool_registry import MCPToolRegistry
from langgraph.checkpoint.memory import InMemorySaver
from .search_graph import build_search_graph
from langgraph.graph import StateGraph, END
from .graph_state import MainGraphState
from langgraph.prebuilt import ToolNode
from langgraph.types import Command
from pathlib import Path
import asyncio
import uuid

# ===============================
# Loading system prompt
# ===============================
BASE_DIR = Path(__file__).resolve().parent
SYSTEM_PROMPT = (BASE_DIR.parent.joinpath("prompts","orchestrator_nav2_system_prompt.xml")).read_text(encoding="utf-8")

async def main():
    try:
        # ===============================
        # MCP Client & Tool, Model Registry Intialization
        # ===============================
        tool_registry = MCPToolRegistry()
        await tool_registry.fetch_tools()

        model_registry = ModelRegistry()
        agent_registry = AgentRegistry(model_registry, tool_registry)

        orchestrator_agent = agent_registry.get_orchestrator_nav2_agent()

        # ===============================
        # Planner Node
        # ===============================
        async def planner(state: MainGraphState):
            print("-" * 30 + "ENTERING PLANNER NODE " + "-" * 30) 
            print(f"🧠 Planner received messages: {state['messages']}")

            system_prompt = SystemMessage(content=SYSTEM_PROMPT)
            response = await orchestrator_agent.ainvoke([system_prompt] + state["messages"])

            print(f"🧠 Planner response: {response}")
            print("\n"+"-" * 30 + "EXITING PLANNER NODE " + "-" * 30) 

            return {"messages": [response]}

        # ===============================
        # Router Node
        # ===============================
        async def router_node(state: MainGraphState):
            print("-" * 30 + "ENTERING ROUTER NODE " + "-" * 30)
            messages = state["messages"]
            last_message = messages[-1]

            if len(last_message.tool_calls) == 0: 
                print("✅ No tool calls detected, finishing execution.")
                return Command(goto=END)

            # Current implementation handles only one tool call per message
            tool_call = last_message.tool_calls[0]
            if tool_call["name"] == "subgraph_dispatch":
                tool_name = tool_call["args"]["subgraph_name"]
                tool_query = tool_call["args"]["query"]
                print(f"🔍 Routing to subgraph based on tool call: {tool_name} with query: {tool_query}\n")
                if tool_name == SubgraphName.SEARCH.value:
                    result = await search_subgraph.ainvoke({"local_messages": [HumanMessage(content=tool_query)]})
                    response = result["local_messages"][-1].content
                    return Command(update={"messages": [ToolMessage(content=response,tool_call_id=tool_call["id"])]}, goto="planner")
                else:
                    return Command(update={"messages": [ToolMessage(content="Subgraph not found")]}, goto="planner")
            else:
                return Command(goto="tools")

        # ===============================
        # Tool Node
        # ===============================
        tool_node = ToolNode(tools=[*tool_registry.get_nav2_tools(), subgraph_dispatch], messages_key="messages")

        # ===============================
        # Build Search Graph
        # ===============================
        search_subgraph = await build_search_graph(tool_registry, agent_registry)
        
        # ===============================
        # Build Graph
        # ===============================
        graph = StateGraph(MainGraphState)

        graph.add_node("planner", planner)
        graph.add_node("router", router_node)
        graph.add_node("tools", tool_node)

        graph.add_edge("planner", "router")
        graph.add_edge("tools", "planner")

        graph.set_entry_point("planner")

        checkpointer = InMemorySaver()
        app = graph.compile(checkpointer=checkpointer)

        # ===============================
        # Accept User Query
        # ===============================
        thread_id = str(uuid.uuid4())
        user_input = input("Enter your query for the robot: ")
        print(f"\n👤 User: {user_input}\n")
        while user_input != "exit":
            result = await app.ainvoke(
                {"messages": [HumanMessage(content=user_input)]},
                {"configurable": {"thread_id": thread_id}},
            )

            # print(f" results[`messages`]: {result['messages']}")
            print(f"\n🤖 Final Answer:\n{result['messages'][-1].content}")

            user_input = input("Enter your query for the robot (type 'exit' to quit): ")

    except Exception as e:
        print(f"❌ Error: {e}")
        raise

    finally:
        print("\n✅ Done")

if __name__ == "__main__":
    asyncio.run(main())