from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import operator
from app.core.config import settings
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from app.tools import research_pubmed

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]

tools= [research_pubmed]
llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=settings.OPENAI_API_KEY)

llm_with_tools = llm.bind_tools(tools)

def reasoner(state: AgentState):
    """
    The Brain: Decides what to do next based on the state.
    """
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

tool_node = ToolNode(tools)

workflow = StateGraph(AgentState)

workflow.add_node("agent", reasoner)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("agent")

def should_continue(state: AgentState):
    """
    Decides whether to continue or end the conversation.
    """
    last_message = state['messages'][-1]

    if last_message.tool_calls:
        return "tools"
    else:
        return END

workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

agent_executor = workflow.compile()