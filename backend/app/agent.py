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
    hallucination_score: str
    context_for_verification: str

class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents"""
    binary_score: str = Field(description="Documents are relevant to the user question, 'yes' or 'no'")  

class RewriteQuery(BaseModel):
    """The new search query."""
    query: str = Field(description="The improved search query to use")

class GradeHallucination(BaseModel):
    """Binary score for hallucination check on generated answer"""
    binary_score: str = Field(description="Answer is grounded in the provided context, 'yes' or 'no'")
    reasoning: str = Field(description="Brief explanation of why the answer is or is not grounded")  

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
    
    # Find the latest user question
    question = messages[0].content
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            question = msg.content
            break

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

    # Find the latest user question
    question = messages[0].content
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            question = msg.content
            break
    
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
    
    # 1. Provide the query: Find last HumanMessage
    question = messages[0].content
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            question = msg.content
            break

    # 2. Gather context for answer generation and verification
    # The tools only return short "Success!" messages, but the agent LLM has the full context
    # So we also capture the agent's last AIMessage which contains the synthesized research
    context_str = ""
    agent_reasoning = ""
    
    print(f"---TOTAL MESSAGES: {len(messages)}---")
    for i, msg in enumerate(messages):
        msg_type = type(msg).__name__
        has_tool_id = hasattr(msg, "tool_call_id")
        print(f"---MSG {i}: {msg_type}, has tool_call_id: {has_tool_id}---")
        if has_tool_id:  # ToolMessage
            content_preview = msg.content[:200] if len(msg.content) > 200 else msg.content
            print(f"---TOOL CONTENT PREVIEW: {content_preview}---")
            context_str += f"\nTool Output: {msg.content}"
        elif isinstance(msg, AIMessage) and not msg.tool_calls and msg.content:
            # Capture the agent's detailed reasoning/synthesis (the last AIMessage without tool calls)
            agent_reasoning = msg.content
    
    # If tools only returned short success messages, use the agent's reasoning as additional context
    if agent_reasoning and len(context_str) < 500:
        print(f"---TOOL OUTPUTS TOO SHORT, ADDING AGENT REASONING ({len(agent_reasoning)} chars)---")
        context_str += f"\n\nAgent's Research Summary:\n{agent_reasoning}"
    
    print(f"---CONTEXT GATHERED: {len(context_str)} chars---")
    
    if not context_str:
        context_str = "No new research data found in this turn. Answer based on available history."

    chain = rag_prompt | rag_llm
    response = chain.invoke({
        "context": context_str,
        "question": question
    })
    
    return {
        "messages": [AIMessage(content=response.answer_summary)],
        "protocols": [p.dict() for p in response.extracted_protocols],
        "context_for_verification": context_str
    }

def hallucination_check_node(state: AgentState):
    """
    Checks if the generated answer is grounded in the retrieved context.
    Detects hallucinations where the LLM made up facts not in the sources.
    """
    print("---CHECKING FOR HALLUCINATIONS---")
    messages = state['messages']
    context = state.get('context_for_verification', '')
    
    print(f"---CONTEXT LENGTH: {len(context)} chars---")
    if not context:
        print("---WARNING: No context found, reconstructing from messages---")
        for msg in messages:
            if hasattr(msg, "tool_call_id"):
                context += f"\nTool Output: {msg.content}"
    
    last_answer = messages[-1].content if messages else ""
    print(f"---ANSWER TO CHECK: {last_answer[:100]}...---")
    
    llm_grader = ChatOpenAI(
        model="gpt-4o", 
        temperature=0, 
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(GradeHallucination)
    
    system = """You are a fact-checker for scientific content. Your job is to verify that an answer is GROUNDED in the provided source documents.

GROUNDED means:
- All facts, numbers, dosages, and claims in the answer can be traced back to the source documents
- The answer does not introduce information that isn't in the sources
- The answer does not exaggerate or misrepresent what the sources say

NOT GROUNDED (hallucination) means:
- The answer contains specific claims (dosages, percentages, species) not found in sources
- The answer makes definitive statements when sources are uncertain
- The answer attributes findings to wrong papers

Be strict. If the answer makes ANY claim that cannot be verified from the context, mark it as NOT grounded."""

    grade_prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", f"""SOURCE DOCUMENTS:
{context}

GENERATED ANSWER:
{last_answer}

Is this answer grounded in the source documents? Respond with 'yes' or 'no' and explain your reasoning."""),
    ])

    grader = grade_prompt | llm_grader
    result = grader.invoke({})

    print(f"---HALLUCINATION CHECK: {result.binary_score} ({result.reasoning})---")
    return {"hallucination_score": result.binary_score}

def decide_after_hallucination_check(state: AgentState):
    """
    Routes based on hallucination check result.
    If grounded -> END
    If hallucination detected -> regenerate with stricter prompt
    """
    score = state.get("hallucination_score", "yes")
    
    if score.lower() == "yes":
        print("---DECISION: ANSWER IS GROUNDED, FINISH---")
        return END
    else:
        print("---DECISION: HALLUCINATION DETECTED, REGENERATING---")
        return "regenerate"

def regenerate_node(state: AgentState):
    """
    Regenerates the answer with a stricter prompt after hallucination was detected.
    """
    print("---REGENERATING ANSWER (STRICTER)---")
    messages = state['messages']
    context = state.get('context_for_verification', '')
    
    question = messages[0].content
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            question = msg.content
            break
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=settings.OPENAI_API_KEY)
    
    strict_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a scientific assistant. Your previous answer contained claims not supported by the sources.
        
STRICT RULES:
1. ONLY include facts that are EXPLICITLY stated in the source documents
2. If a specific number (dosage, percentage) is not in the sources, say "the exact value was not specified"
3. Use phrases like "according to the study" or "the paper reports" to cite specific claims
4. If you're unsure about something, say so rather than guessing
5. DO NOT extrapolate or generalize beyond what the sources say"""),
        ("human", f"""Based ONLY on these source documents, answer the question.

SOURCE DOCUMENTS:
{context}

QUESTION: {question}

Provide a grounded answer that only includes information from the sources."""),
    ])

    chain = strict_prompt | llm
    response = chain.invoke({})
    
    return {
        "messages": [AIMessage(content=response.content)],
        "hallucination_score": "yes"
    }

workflow.add_node("answer_gen", answer_gen_node)
workflow.add_node("hallucination_check", hallucination_check_node)
workflow.add_node("regenerate", regenerate_node)

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        END: "answer_gen"
    }
)

workflow.add_edge("answer_gen", "hallucination_check")

workflow.add_conditional_edges(
    "hallucination_check",
    decide_after_hallucination_check,
    {
        END: END,
        "regenerate": "regenerate"
    }
)

workflow.add_edge("regenerate", END)

redis_client = Redis(host="localhost", port=6379, db=0)
checkPointer = RedisSaver(redis_client=redis_client)
checkPointer.setup() 

agent_executor = workflow.compile(checkpointer=checkPointer)