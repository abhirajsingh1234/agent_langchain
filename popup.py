from langchain.agents import initialize_agent, Tool
from langchain.agents.agent_types import AgentType
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
import os
from langchain_ollama import ChatOllama
from langchain.schema import HumanMessage, AIMessage
from pydantic import BaseModel
from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchRun
from whatsapp_tool import send_whatsapp_message_tool
load_dotenv()
google_api_key = os.getenv('GEMINI_API_KEY')

# Step 1: Initialize LLM and prompt template
template = ChatPromptTemplate(
    messages=[
        ('system', """You are a users friend.
                        talk like a pirate.
                        if user says hyy , reply with 'aye aye captain'
                        Use the appropriate tool when needed.
                        If no tool is applicable, generate a friendly response directly.
                        You have access to past memory.
                        Use your memory to recall past conversations and provide relevant context.
                        """),
        MessagesPlaceholder(variable_name="chat_history"),
        ('user', '{input}')
    ]
)

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", api_key=google_api_key)
# llm = ChatOllama(model="gemma3:4b")


# Step 2: Define tools
class validator(BaseModel):
    expression: str

@tool(args_schema=validator)
def basic_calculator(expression: str) -> str:
    """Evaluate a basic math expression (e.g. 2 + 2, 5*6)"""
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {e}"

@tool(args_schema=validator)
def search_tool(expression: str) -> str:
    """A search tool for returning search results."""
    try:
        search_tool = DuckDuckGoSearchRun()
        response = search_tool.run(expression)
        return response
    except Exception as e:
        return f"Error during search: {e}"

@tool(args_schema=validator)
def send_whatsapp_message(expression: str) ->str:
    """Send a WhatsApp message to a specified phone number or contact name."""
    result = send_whatsapp_message_tool(expression)
    return result


# Step 3: Register tools
tools = [
    Tool.from_function(
        func=basic_calculator,
        name="Calculator",
        description="Use this tool when you need to perform mathematical calculations."
    ),
    Tool.from_function(
        func=search_tool,
        name="Search",
        description="Use this tool when you need to search for information online."
    ),
    Tool.from_function(
        func=send_whatsapp_message,
        name="whatsapp_message_sender",
        description="Send a WhatsApp message. Input should be a sentence with the message and recipient."
    )
]

# Step 4: Initialize memory with conversation buffer
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    output_key="output"     #only stores the final output key of response
)

# Step 5: Initialize the Agent with memory
chain = template | llm
agent = initialize_agent(
    tools,
    llm,
    # agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,  #Chatty agents with memory	
    # agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,      #Simple tool-using agents	
    # agent=AgentType.OPENAI_FUNCTIONS,     #Structured APIs & function-style tools	
    # agent=AgentType.OPENAI_MULTI_FUNCTIONS,   #Multiple tools per call (OpenAI only)
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,  #Structured APIs & function-style tools	

    memory=memory,  # Add memory to the agent
    agent_kwargs={'chain': chain},    #pass the chain to agent
    verbose=True,     #enables you to see the agent's internal thought process
    handle_parsing_errors=True  # Helps with parsing errors
)

# Step 6: Main conversation loop
print("Chat with the agent (type 'exit' to quit)")
print("Type 'remember X' to test memory recall about topic X")

while True:
    query = input('You: ')
    if query.lower() == 'exit':
        break
    
    # Invoke agent with input
    try:
        response = agent.invoke({"input": query})
        output = response['output']
        print(f"Agent: {output}")
    except Exception as e:
        print(f"Error: {e}")
        print("Let me try again with a simpler approach.")
        # Fallback for errors
        direct_response = llm.invoke(f"The user asked: {query}. Provide a helpful response like a pirate.")
        memory.chat_memory.add_message(HumanMessage(content=query))
        memory.chat_memory.add_message(AIMessage(content=direct_response.content))
        print(f"Agent: {direct_response.content}")

print(memory)
print(f"Memory buffer: {memory.buffer}")