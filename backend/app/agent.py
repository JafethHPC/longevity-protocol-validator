from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
import operator
from app.core.config import settings
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from app.tools import research_pubmed, research_visuals
from redis import Redis
from langgraph.checkpoint.redis import RedisSaver
from pydantic import BaseModel, Field

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    quality: str
    protocols: Annotated[List[dict], operator.add]

class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents"""
    binary_score: str = Field(description="Documents are relevant to the user question, 'yes' or 'no'")  

class RewriteQuery(BaseModel):
    """The new search query."""
    query: str = Field(description="The improved search query to use")  

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
    print("---AGENT REASONING---")
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]

    response = llm_with_tools.invoke(messages)
    print(f"---AGENT RESPONSE: {response.content} (Tool Calls: {response.tool_calls})---")
    
    return {"messages": [response]}

def should_continue(state: AgentState):
    """
    Decides whether to continue or end the conversation.
    """
    last_message = state['messages'][-1]

    if last_message.tool_calls:
        print("---DECISION: CALL TOOLS---")
        return "tools"
    else:
        print("---DECISION: FINISH---")
        return END

def decide_to_generate(state: AgentState):
    """
    Determines whether to generate an answer or re-try search.
    """
    quality = state.get("quality", "yes")

    if quality == "yes":
        print("---DECISION: GENERATE ANSWER---")
        return "agent"
    else:
        print("---DECISION: RE-TRY SEARCH---")
        return "rewrite"

def grading_node(state: AgentState):
    """
    Determines if the retrieved documemnts are relevant to the question. 
    If not, it re-writes the search query.
    """
    print("---CHECKING RELEVANCE---")
    messages = state['messages']
    last_tool_msg = messages[-1]

    if not isinstance(last_tool_msg, BaseMessage):
        return {"quality": "yes"}
    
    question = messages[0].content
    documents = last_tool_msg.content

    llm_grader = ChatOpenAI(model="gpt-4o", temperature=0, api_key=settings.OPENAI_API_KEY).with_structured_output(GradeDocuments)
    
    system = """You are a grader assessing relevance of a retrieved document to a user question. 
    If the document contains keyword(s) or semantic meaning related to the question, grade it as relevant. 
    Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""

    grade_prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", f"Retrieved document: \n\n {documents} \n\n User question: {question}"),
    ])

    grader = grade_prompt | llm_grader
    score = grader.invoke({})

    print(f"---GRADE: {score.binary_score}---")
    return {"quality": score.binary_score}

def rewrite_retrieve_node(state: AgentState):
    """
    Refines the search query if the inital search yielded irrelevant results.
    """
    print("---RE-WRITING SEARCH QUERY---")
    messages = state['messages']
    question = messages[0].content
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=settings.OPENAI_API_KEY)

    structured_llm = llm.with_structured_output(RewriteQuery)

    system = """You are a query re-writer that converts an input question to a better version that is optimized 
    for searching scientific literature (PubMed/Vector Search). Look at the initial input and try to extract 
    better keywords or synonyms."""

    re_write_prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", f"Initial Question: {question} \n Formulate an improved search query."),    ])

    chain = re_write_prompt | structured_llm
    response = chain.invoke({})

    return {"messages": [HumanMessage(content=response.query)]}

tool_node = ToolNode(tools)
workflow = StateGraph(AgentState)

workflow.add_node("agent", reasoner)
workflow.add_node("tools", tool_node)
workflow.add_node("grader", grading_node)
workflow.add_node("rewrite", rewrite_retrieve_node)

workflow.set_entry_point("agent")
workflow.add_edge("tools", "grader")
workflow.add_edge("rewrite", "agent")

workflow.add_conditional_edges(
    "grader", 
    decide_to_generate, 
    {
        "agent": "agent",
        "rewrite": "rewrite" 
    }
)
    
def answer_gen_node(state: AgentState):
    """
    Final node: Generates the structured answer using Pydantic schema
    based on all gathered context.
    """
    print("---GENERATING FINAL STRUCTURED ANSWER---")
    messages = state['messages']
    
    from app.rag import prompt as rag_prompt, llm as rag_llm
    
    context_str = ""
    for msg in messages:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            context_str += f"\nAgent Planned: {msg.tool_calls}"
        elif hasattr(msg, "tool_call_id"): # ToolMessage
            context_str += f"\nTool Output: {msg.content}"
    
    if not context_str:
        context_str = str(messages)

    chain = rag_prompt | rag_llm
    response = chain.invoke({
        "context": context_str,
        "question": messages[0].content
    })
    
    return {
        "messages": [AIMessage(content=response.answer_summary)],
        "protocols": [p.dict() for p in response.extracted_protocols]
    }

workflow.add_node("answer_gen", answer_gen_node)

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        END: "answer_gen"
    }
)
workflow.add_edge("answer_gen", END)

redis_client = Redis(host="localhost", port=6379, db=0)
checkPointer = RedisSaver(redis_client=redis_client)
checkPointer.setup() 

agent_executor = workflow.compile(checkpointer=checkPointer)