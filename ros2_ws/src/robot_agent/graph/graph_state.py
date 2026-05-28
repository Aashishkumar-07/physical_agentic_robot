from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from typing import Annotated, List, TypedDict
    
# ===============================
# Main graph State
# ===============================
class MainGraphState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

# ===============================
# Search graph State
# ===============================
class SearchGraphState(TypedDict):
    local_messages: Annotated[List[BaseMessage],add_messages]

