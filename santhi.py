import asyncio
from dotenv import load_dotenv
load_dotenv()

# -------------------------
# Set up the API Agent (RequestsToolkit)
# -------------------------
from langchain_community.agent_toolkits.openapi.toolkit import RequestsToolkit
from langchain_community.utilities.requests import TextRequestsWrapper
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from browser_use import Agent
# Enable dangerous requests (use with caution)
ALLOW_DANGEROUS_REQUEST = True

# Set up the requests wrapper with custom headers (e.g., for authentication)
headers = {"Authorization": "Bearer YOUR_API_TOKEN"}
requests_wrapper = TextRequestsWrapper(headers=headers)

# Instantiate the RequestsToolkit
toolkit = RequestsToolkit(
    requests_wrapper=requests_wrapper,
    allow_dangerous_requests=ALLOW_DANGEROUS_REQUEST,
)

# Get the API tools (GET, POST, etc.)
api_tools = toolkit.get_tools()

# Initialize the LLM for the API agent
llm_api = ChatOpenAI(model="gpt-4o")

# Create the API agent (synchronous)
api_agent = initialize_agent(
    tools=api_tools,
    llm=llm_api,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# -------------------------
# Set up the Browser Agent (browser_use.Agent)
# -------------------------

# Define the initial browser task

# -------------------------
# Wrap each agent as a tool for the Coordinator Agent
# -------------------------
# For the API agent (synchronous)
def run_api_agent_tool(query: str) -> str:
    return api_agent.run(query)


from langchain.agents import tool


@tool
def api_agent_tool(query: str) -> str:
    """
    This tool calls the API agent to perform HTTP requests.
    Input: A string query describing the API call.
    Output: The API response as text.
    """
    return run_api_agent_tool(query)

# For the Browser agent (asynchronous, wrapped for synchronous calls)
def run_browser_agent_tool(query: str) -> str:

    # Initialize the LLM for the Browser agent (can be the same model)
    llm_browser = ChatOpenAI(model="gpt-4o")

    # Create the Browser agent (asynchronous)
    browser_agent = Agent(
        task=query,
        llm=llm_browser
    )
    return asyncio.run(browser_agent.run())

@tool
def browser_agent_tool(query: str) -> str:
    """
    This tool calls the Browser agent to perform browser automation.
    Input: A string query describing the browser task.
    Output: The browser agent's result.
    """
    return run_browser_agent_tool(query)

# -------------------------
# Set up the Coordinator Agent
# -------------------------
# Initialize an LLM for coordination
llm_coordinator = ChatOpenAI(model="gpt-4o")

# Provide the two wrapped tools to the coordinator
tools = [api_agent_tool, browser_agent_tool]

# Create the coordinator agent using a ReAct-style agent
coordinator_agent = initialize_agent(
    tools=tools,
    llm=llm_coordinator,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# -------------------------
# High-Level Coordination: Run the Coordinator Agent
# -------------------------
high_level_instruction = (
    "I need to retrieve data from https://fakerapi.it/api/v2/persons?_quantity=5 and then  use that data to fill out a Google Form at  https://docs.google.com/forms/d/e/1FAIpQLSfuzbOAoGVJSa82VVbnMj0InzUdiugOC_Wt8_Hce-huuGCBkA/viewform . Plan the actions needed and execute them."
)

# Run the coordinator agent with the high-level instruction
result = coordinator_agent.run(high_level_instruction)
print("Coordinator Agent Final Result:\n", result)