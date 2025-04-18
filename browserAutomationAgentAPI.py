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
from langchain.agents import tool
from jira import JIRA

ALLOW_DANGEROUS_REQUEST = True


# Enter you credentials...
JIRA_SERVER = ''
EMAIL = ''  # Your Atlassian email
API_TOKEN = ''      # From https://id.atlassian.com/manage/api-tokens

jira = JIRA(
    server=JIRA_SERVER,
    basic_auth=(EMAIL, API_TOKEN)
)
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
llm = ChatOpenAI(model="gpt-4o")
api_agent = initialize_agent(
    tools=api_tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

def run_api_agent_tool(query: str) -> str:
    return api_agent.run(query)


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
    verbose=True,
    handle_parsing_errors=True
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
    return jsonify({"result": result})

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
    result = coordinator_agent.invoke(query).content
    return jsonify({"result": result})


@app.route('/coordinator-agent-bdd-file', methods=['POST'])
def coordinator_agent_bdd_file_endpoint():
    """
    Coordinator Agent with BDD Feature File (File Upload) Endpoint
    ---
    tags:
      - Coordinator Agent
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: bdd_file
        type: file
        required: true
        description: "The BDD feature file to be used"
    responses:
      200:
        description: Successful response from the Coordinator agent with BDD instructions applied.
        schema:
          type: object
          properties:
            result:
              type: string
              example: "Response from Coordinator agent"
    """
    # Generic high-level instruction to be used
    generic_instruction = "Proceed with the coordinated task."

    # Get the uploaded BDD file
    bdd_file = request.files.get("bdd_file")
    if bdd_file:
        # Read and decode the file contents (assuming it's UTF-8 encoded)
        bdd_instructions = bdd_file.read().decode("utf-8")
    else:
        bdd_instructions = ""

    # Combine the BDD feature file content with the generic instruction.
    full_instruction = (
            "Please follow the instructions in the following BDD feature file when executing this task:\n\n and make sure to use"
            "existing tools to execute the task" +
            bdd_instructions +
            "\n\n" + generic_instruction
    )

    # Run the coordinator agent with the combined instruction.
    result = coordinator_agent.run(full_instruction)
    return jsonify({"result": result})


@app.route('/execute-jira-feature/<issue_key>')
def execute_jira_feature(issue_key):
    """
    Generate a descriptive Gherkin feature file from a Jira ticket key,
    save it to disk, then have the agent execute it.
    ---
    parameters:
      - in: path
        name: issue_key
        type: string
        required: true
        description: The Jira ticket key, e.g. RD-1
    responses:
      200:
        description: Feature file generated, saved, and executed.
        schema:
          type: object
          properties:
            feature_file_path:
              type: string
            agent_result:
              type: string
    """
    # 1. Fetch Jira issue
    try:
        issue = jira.issue(issue_key)
    except Exception as e:
        return jsonify({"error": f"Could not fetch {issue_key}: {e}"}), 400

    # 2. Extract the fields you care about
    summary     = issue.fields.summary or ""
    description = issue.fields.description or ""
    status      = issue.fields.status.name
    assignee    = issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned"
    created     = issue.fields.created
    updated     = issue.fields.updated

#     # 3. Ask the LLM to build a *very descriptive* feature file
#     prompt_to_generate_feature = f"""
#             You are a BDD expert. Generate a  Gherkin feature file, by using the folllowing info
#             Ticket data:
#               Key: {issue_key}
#               Summary: {summary}
#               Description: {description}
# """
#     # this returns a multi‑line Gherkin string
#     feature_text = llm.invoke(prompt_to_generate_feature).content
#     feature_text = feature_text.replace("```gherkin\n", "").replace("```", "")
    feature_text=description
    print(feature_text)

    # 4. Save it to disk
    feature_filename = f"{issue_key}.feature"
    with open(feature_filename, "w", encoding="utf-8") as fd:
        fd.write(feature_text)

    # 5. Now execute that feature file via the same agent
    execute_prompt = f"""
You have exactly two tools:

> browser_agent_tool(query: str) -> str  
>   Use this for any browser/UI interaction: open URLs, click, type, assert page content.

> api_agent_tool(query: str) -> str  
>   Use this for any HTTP/API interaction: GET, POST, inspect JSON, check status codes.

Execute this feature **step by step**.  
For each line that begins with Given/When/And/Then:
  - If it’s a UI action, invoke:
      browser_agent_tool("<that exact step text>")
  - If it’s an API action, invoke:
      api_agent_tool("<that exact step text>")

Do **not** print any explanation—only the tool calls themselves, in sequence.

When you’ve finished all steps, output **only** this JSON object (no markdown, no extra text):
```json
{{
  "feature": "{issue_key}.feature",
  "steps_executed": <total_steps>,
  "errors": [
    {{ "step": "<step text>", "error": "<error message>" }},
    …
  ]
}}
Here is the feature to run:

Copy
Edit
{feature_text}
"""
    agent_result = coordinator_agent.run(execute_prompt)

    # 6. Return both the path to the saved file and the agent’s execution result
    return jsonify({
        "feature_file_path": feature_filename,
        "agent_result": agent_result
    })


if __name__ == '__main__':
    app.run(debug=True)
