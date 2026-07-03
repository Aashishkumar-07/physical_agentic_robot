from ..dispatcher.subgraph_dispatcher_tool import subgraph_dispatch
from langchain.chat_models import init_chat_model
from .mcp_tool_registry import MCPToolRegistry
from pydantic import BaseModel
from typing import Optional

# ===============================
# Structured Outputs
# ===============================
class SearchSummary(BaseModel):
    coordinate: dict
    keywords: list[str]
    score: float

class RetrievalDecision(BaseModel):
    reasoning: str
    selected_targets: Optional[list[SearchSummary]]

# ===============================
# Model Registry
# ===============================
class ModelRegistry:
    def __init__(self):
        self.chat_model = init_chat_model(model="qwen3:8b",model_provider="ollama")

# ===============================
# Register agents from registered model
# ===============================
class AgentRegistry:
    def __init__(self, model: ModelRegistry, tool_registry: MCPToolRegistry):
        self.model = model.chat_model
        self.tools = tool_registry

    def get_nav2_agent(self):
        return self.model.bind_tools(self.tools.get_nav2_tools())

    def get_orchestrator_nav2_agent(self):
        return self.model.bind_tools([*self.tools.get_nav2_tools(), subgraph_dispatch])


    def get_faiss_agent(self):
        return self.model.bind_tools(self.tools.get_faiss_tools())
    
    def get_evaluator_agent(self):
        return self.model.with_structured_output(RetrievalDecision)
