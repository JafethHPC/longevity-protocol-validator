from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
import operator
from app.core.config import settings
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from app.tools import research_pubmed, research_visuals
from redis import Redis
from langgraph.checkpoint.redis import RedisSaver

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]

tools= [research_pubmed, research_visuals]
llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=settings.OPENAI_API_KEY)

llm_with_tools = llm.bind_tools(tools)

SYSTEM_PROMPT = """You are an elite Autonomous Researcher.
Your goal is to provide comprehensive scientific answers backed by data.

RULES FOR CITATION:
1. You have access to multiple papers. DO NOT mix them up.
2. If you cite a fact (like dosage), you must check if it comes from the SAME paper as the visual you are discussing.
3. If Fact A comes from Paper X and Figure B comes from Paper Y, you must explicitly say:
   "Paper X used a dosage of [amount], while Figure B from Paper Y shows survival curves..."

STRATEGY:
1. When a user asks to research a topic, you should ALWAYS try to gather two types of evidence:
    - Textual Evidence: Use 'research_pubmed' to get abstracts.
    - Visual Evidence: Use 'research_visuals' to get charts and figures.

2. Execute these tools in parallel if possible.
3. Once you have the data, synthesize a final answer that cites both the papers and the scientific figures found.
"""

def reasoner(state: AgentState):
    """
    The Brain: Decides what to do next based on the state.
    """
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]

    response = llm_with_tools.invoke(messages)

    return {"messages": [response]}

def should_continue(state: AgentState):
    """
    Decides whether to continue or end the conversation.
    """
    last_message = state['messages'][-1]

    if last_message.tool_calls:
        return "tools"
    else:
        return END

tool_node = ToolNode(tools)

workflow = StateGraph(AgentState)
workflow.add_node("agent", reasoner)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

redis_client = Redis(host="localhost", port=6379, db=0)
checkPointer = RedisSaver(redis_client=redis_client)
checkPointer.setup()  # Initialize Redis indices

agent_executor = workflow.compile(checkpointer=checkPointer)