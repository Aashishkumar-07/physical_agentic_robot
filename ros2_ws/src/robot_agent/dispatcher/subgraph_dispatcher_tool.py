from langchain_core.tools import tool
from enum import Enum

# ===============================
# Subgraph ENUM
# ===============================
class SubgraphName(str, Enum):
    SEARCH = "search_subgraph"

# ===============================
# Subgraph Orchestration Tool  
# ===============================
@tool
def subgraph_dispatch(subgraph_name: SubgraphName, query: str) :
    """
    Delegate a task to a specialized subgraph.
    Use:
    - search_subgraph:
    Use when the user asks about previously observed objects, locations, spatial relationships, or historical warehouse observations.
    The search subgraph can retrieve relevant prior observations and contextual information to support navigation or reasoning.
    """


