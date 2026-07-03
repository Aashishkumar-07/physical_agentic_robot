from langchain_core.messages import (AIMessage, SystemMessage)
from robot_agent.registry.mcp_tool_registry import MCPToolRegistry
from robot_agent.registry.model_registry import AgentRegistry
from robot_agent.graph.graph_state import SearchGraphState
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from pathlib import Path

# ===============================
# Loading system prompt
# ===============================
BASE_DIR = Path(__file__).resolve().parent
EVALUATOR_SYSTEM_PROMPT = (BASE_DIR.parent.joinpath("prompts","evaluator_system_prompt.xml")).read_text(encoding="utf-8")
SEARCH_SYSTEM_PROMPT = (BASE_DIR.parent.joinpath("prompts", "search_system_prompt.xml")).read_text(encoding="utf-8")

async def build_search_graph(tool_registry: MCPToolRegistry, agent_registry: AgentRegistry):
    try:
        evaluator_agent =  agent_registry.get_evaluator_agent()
        search_agent = agent_registry.get_faiss_agent()

        # ===============================
        # Planner Node
        # ===============================
        async def search_planner(state: SearchGraphState):

            print("-" * 30 + "ENTERING SEARCH PLANNER NODE " + "-" * 30) 
            print("local_messages:", state["local_messages"])

            system_prompt = SystemMessage(content=SEARCH_SYSTEM_PROMPT)
            response = await search_agent.ainvoke([system_prompt, *state["local_messages"]])

            print(f"🧠 Search Planner response: {response}")
            print("\n"+"-" * 30 + "EXITING SEARCH PLANNER NODE " + "-" * 30) 

            return {"local_messages": [response]}
        
        # ===============================
        # Conditional Edge Router
        # ===============================
        def planner_router(state: SearchGraphState) :
            messages = state["local_messages"]
            last_message = messages[-1]

            if len(last_message.tool_calls) > 0: 
                return "tools"
                
            print("✅ No tool calls detected, finishing execution.")
            return END
    
        def tool_router(state: SearchGraphState):
            last_message = state["local_messages"][-1]
            print(f"🔍 Routing based on tool call: {last_message}\n")
            tool_name = last_message.name
            if tool_name == "faiss_search":
                    return "summarizer"

            return "search_planner"
        
        # ===============================
        # Summarizer Node
        # ===============================
        async def summarizer_evaluator(state: SearchGraphState):
            print("-" * 30 + "ENTERING SUMMARIZER/EVALUATOR NODE " + "-" * 30) 
            print(f"🧠 Summarizer/Evaluator received messages: {state['local_messages']}")

            response = await evaluator_agent.ainvoke([
                SystemMessage(content=EVALUATOR_SYSTEM_PROMPT),
                *state["local_messages"]
                ])
            print(f"🧠 Summarizer/Evaluator response: {response}")
            print("-" * 30 + "EXITING SUMMARIZER/EVALUATOR NODE " + "-" * 30) 
            return {"local_messages" : [AIMessage(content=response.model_dump_json())]}
            
        # ===============================
        # Tool Node
        # ===============================
        tool_node = ToolNode(tools=tool_registry.get_faiss_tools(), messages_key="local_messages")

        # ===============================
        # Build graph
        # ===============================
        search_graph = StateGraph(SearchGraphState)

        search_graph.add_node("search_planner",search_planner)
        search_graph.add_node("search_tools", tool_node)
        search_graph.add_node("summarizer", summarizer_evaluator)  
         
        search_graph.set_entry_point("search_planner")

        search_graph.add_edge("summarizer", END)
        search_graph.add_conditional_edges(
            "search_planner",
            planner_router,
            {
                "tools": "search_tools",
                END: END
            }
        )
        search_graph.add_conditional_edges(
            "search_tools",
            tool_router,
            {
                "summarizer": "summarizer",
                "search_planner": "search_planner"
            }
        )

        return search_graph.compile(checkpointer=None)      
      
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

