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
from browser_use import Agent  # Assuming this is your browser automation agent

# Enable dangerous requests (use with caution)
ALLOW_DANGEROUS_REQUEST = True

# Set up the requests wrapper with custom headers (e.g., for authentication)
headers = {"Authorization": "Bearer YOUR_API_TOKEN"}
requests_wrapper = TextRequestsWrapper(headers=headers)

# Instantiate the RequestsToolkit and get the API tools
toolkit = RequestsToolkit(
    requests_wrapper=requests_wrapper,
    allow_dangerous_requests=ALLOW_DANGEROUS_REQUEST,
)
api_tools = toolkit.get_tools()

# Initialize the LLM for the API agent and create the agent
llm_api = ChatOpenAI(model="gpt-4o")
api_agent = initialize_agent(
    tools=api_tools,
    llm=llm_api,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

def run_api_agent_tool(query: str) -> str:
    return api_agent.run(query)

from langchain.agents import tool

@tool
def api_agent_tool(query: str) -> str:
    """
    This tool calls the API agent to perform HTTP requests.
    """
    return run_api_agent_tool(query)

# -------------------------
# Set up the Browser Agent (browser_use.Agent)
# -------------------------
def run_browser_agent_tool(query: str) -> str:
    # Initialize the LLM for the Browser agent (can be the same model)
    llm_browser = ChatOpenAI(model="gpt-4o")
    # Create the Browser agent (asynchronous)
    browser_agent = Agent(
        task=query,
        llm=llm_browser,
    )
    return asyncio.run(browser_agent.run())

@tool
def browser_agent_tool(query: str) -> str:
    """
    This tool calls the Browser agent to perform browser automation.
    """
    return run_browser_agent_tool(query)

# -------------------------
# Set up the Coordinator Agent
# -------------------------
# Initialize an LLM for coordination and create the coordinator agent
llm_coordinator = ChatOpenAI(model="gpt-4o")
tools = [api_agent_tool, browser_agent_tool]
coordinator_agent = initialize_agent(
    tools=tools,
    llm=llm_coordinator,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# -------------------------
# Expose as API Endpoints using Flask with Flasgger for Swagger docs
# -------------------------
from flask import Flask, request, jsonify
from flasgger import Swagger

app = Flask(__name__)
swagger = Swagger(app)  # Swagger UI available at /apidocs

@app.route('/api-agent', methods=['POST'])
def api_agent_endpoint():
    """
    API Agent Endpoint
    ---
    tags:
      - API Agent
    consumes:
      - application/json
    parameters:
      - in: body
        name: payload
        description: JSON payload containing the query for the API agent.
        required: true
        schema:
          type: object
          properties:
            query:
              type: string
              example: "Your API query here"
    responses:
      200:
        description: Successful response from the API agent
        schema:
          type: object
          properties:
            result:
              type: string
              example: "Response from API agent"
    """
    data = request.get_json()
    query = data.get("query", "")
    result = run_api_agent_tool(query)
    return jsonify({"result": "API Agent invoked successfullys"})

@app.route('/browser-agent', methods=['POST'])
def browser_agent_endpoint():
    """
    Browser Agent Endpoint
    ---
    tags:
      - Browser Agent
    consumes:
      - application/json
    parameters:
      - in: body
        name: payload
        description: JSON payload containing the query for the Browser agent.
        required: true
        schema:
          type: object
          properties:
            query:
              type: string
              example: "Your browser task here"
    responses:
      200:
        description: Successful response from the Browser agent
        schema:
          type: object
          properties:
            result:
              type: string
              example: "Response from Browser agent"
    """
    data = request.get_json()
    query = data.get("query", "")
    run_browser_agent_tool(query)
    return jsonify({"result": "Browser agent invoked sucessfully"})

@app.route('/coordinator-agent', methods=['POST'])
def coordinator_agent_endpoint():
    """
    Coordinator Agent Endpoint
    ---
    tags:
      - Coordinator Agent
    consumes:
      - application/json
    parameters:
      - in: body
        name: payload
        description: JSON payload containing the high-level instruction for the Coordinator agent.
        required: true
        schema:
          type: object
          properties:
            query:
              type: string
              example: "Your high-level instruction here"
    responses:
      200:
        description: Successful response from the Coordinator agent
        schema:
          type: object
          properties:
            result:
              type: string
              example: "Response from Coordinator agent"
    """
    data = request.get_json()
    query = data.get("query", "")
    result = coordinator_agent.run(query)
    return jsonify({"result": result})

if __name__ == '__main__':
    app.run(debug=True)
