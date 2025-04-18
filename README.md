# Multi-Agent System with API, Browser, and Coordinator Agents

This project implements a multi-agent system that integrates API interactions, browser automation, and a coordinator agent to execute tasks, including those defined in Behavior-Driven Development (BDD) feature files. It uses Flask to expose the agents as API endpoints and integrates with Jira for fetching and executing tasks based on Jira tickets. The system is designed to be extensible and supports Swagger documentation for API interaction.

## Features

- **API Agent**: Handles HTTP requests (GET, POST, etc.) using the LangChain `RequestsToolkit`.
- **Browser Agent**: Performs browser automation tasks (e.g., opening URLs, clicking elements) using a custom browser agent.
- **Coordinator Agent**: Orchestrates tasks by delegating to the API or Browser agent based on the task requirements.

**Jira Integration**: Fetches Jira tickets and generates/executes Gherkin feature files based on ticket data.

- **Flask API**: Exposes agent functionalities as RESTful endpoints with Swagger documentation.
- **BDD Support**: Executes tasks defined in Gherkin feature files, supporting step-by-step execution.

## Prerequisites

- Python 3.8+

- A Jira account with an API token (generated at https://id.atlassian.com/manage/api-tokens)

- An OpenAI API key for the ChatOpenAI model

- A `.env` file with the following environment variables:

  ```
  OPENAI_API_KEY=your_openai_api_key
  ```

## Installation

1. Clone the repository:

   ```bash
   git clone <repository_url>
   cd <repository_directory>
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root and add your OpenAI API key:

   ```bash
   echo "OPENAI_API_KEY=your_openai_api_key" > .env
   ```

## Dependencies

The project requires the following Python packages (listed in `requirements.txt`):

```
langchain
langchain-community
langchain-openai
jira
flask
flasgger
python-dotenv
```

Install them using:

```bash
pip install langchain langchain-community langchain-openai jira flask flasgger python-dotenv
```

## Configuration

- **Jira Setup**: Update the `JIRA_SERVER`, `EMAIL`, and `API_TOKEN` variables in the code with your Jira instance details.

  ```python
  JIRA_SERVER = 'https://your-jira-instance.atlassian.net'
  EMAIL = 'your-email@example.com'
  API_TOKEN = 'your_jira_api_token'
  ```

- **OpenAI API**: Ensure the `OPENAI_API_KEY` is set in the `.env` file.

- **Custom Headers**: Modify the `headers` dictionary in the code if additional API authentication is needed:

  ```python
  headers = {"Authorization": "Bearer YOUR_API_TOKEN"}
  ```

## Running the Application

1. Start the Flask server:

   ```bash
   python app.py
   ```

   The application will run on `http://127.0.0.1:5000` by default.

2. Access the Swagger UI for API documentation:

   - Open `http://127.0.0.1:5000/apidocs` in your browser.
   - The Swagger UI provides interactive documentation for the `/api-agent`, `/browser-agent`, `/coordinator-agent`, `/coordinator-agent-bdd-file`, and `/execute-jira-feature/<issue_key>` endpoints.

3. Test the endpoints using tools like `curl`, Postman, or the Swagger UI:

   - **API Agent**:

     ```bash
     curl -X POST http://127.0.0.1:5000/api-agent -H "Content-Type: application/json" -d '{"query": "Your API query here"}'
     ```

   - **Browser Agent**:

     ```bash
     curl -X POST http://127.0.0.1:5000/browser-agent -H "Content-Type: application/json" -d '{"query": "Your browser task here"}'
     ```

   - **Coordinator Agent**:

     ```bash
     curl -X POST http://127.0.0.1:5000/coordinator-agent -H "Content-Type: application/json" -d '{"query": "Your high-level instruction here"}'
     ```

   - **BDD File Upload**:

     ```bash
     curl -X POST http://127.0.0.1:5000/coordinator-agent-bdd-file -F "bdd_file=@path/to/your/feature.file"
     ```

   - **Jira Feature Execution**:

     ```bash
     curl http://127.0.0.1:5000/execute-jira-feature/RD-1
     ```

## Code Structure

- **API Agent**: Uses LangChain’s `RequestsToolkit` to handle HTTP requests. Configured with custom headers for authentication.
- **Browser Agent**: Custom agent (`browser_use.Agent`) for browser automation, supporting tasks like navigating websites or interacting with UI elements.
- **Coordinator Agent**: Orchestrates tasks by selecting the appropriate tool (API or Browser agent) based on the task context. Handles parsing errors and verbose logging.
- **Jira Integration**: Connects to a Jira instance to fetch ticket details, generates Gherkin feature files, and executes them using the coordinator agent.
- **Flask Endpoints**: Exposes agent functionalities as RESTful APIs with Swagger documentation for easy interaction.
- **BDD Execution**: Supports uploading and executing Gherkin feature files, with step-by-step execution using the coordinator agent.

## Example Usage

### Running a Jira Feature

1. Ensure your Jira credentials are configured in the code.

2. Call the Jira feature endpoint with a valid Jira issue key (e.g., `RD-1`):

   ```bash
   curl http://127.0.0.1:5000/execute-jira-feature/RD-1
   ```

3. The system will:

   - Fetch the Jira ticket details.
   - Generate a Gherkin feature file based on the ticket’s summary and description.
   - Save the feature file to disk (e.g., `RD-1.feature`).
   - Execute the feature file step-by-step using the coordinator agent.
   - Return the feature file path and execution result.

### Executing a BDD Feature File

1. Create a Gherkin feature file (e.g., `example.feature`):

   ```gherkin
   Feature: Example Feature
     Scenario: Test API and Browser
       Given I make a GET request to https://api.example.com
       When I navigate to https://example.com
       Then I verify the page contains "Welcome"
   ```

2. Upload and execute the feature file:

   ```bash
   curl -X POST http://127.0.0.1:5000/coordinator-agent-bdd-file -F "bdd_file=@example.feature"
   ```

3. The coordinator agent will execute the steps, delegating API steps to the API agent and browser steps to the browser agent.

## Notes

- **Security**: The `ALLOW_DANGEROUS_REQUEST` flag is set to `True` for the `RequestsToolkit`. Use caution in production environments to avoid unintended API calls.
- **Browser Agent**: The `browser_use.Agent` implementation is assumed to be a custom module. Ensure it is properly implemented and compatible with the project.
- **Error Handling**: The coordinator agent includes parsing error handling, but ensure robust error handling in production.
- **Jira API Token**: Store the Jira API token securely (e.g., in the `.env` file) instead of hardcoding it in the code.
- **Scalability**: For production, consider deploying the Flask app with a WSGI server like Gunicorn and using a reverse proxy like Nginx.

## Troubleshooting

- **Jira Connection Issues**: Verify the `JIRA_SERVER`, `EMAIL`, and `API_TOKEN` values. Ensure the API token is valid and has the necessary permissions.
- **OpenAI API Errors**: Check the `OPENAI_API_KEY` in the `.env` file and ensure you have sufficient API credits.
- **Flask Server Not Starting**: Ensure all dependencies are installed and there are no port conflicts (default port is 5000).
- **BDD Execution Failures**: Verify the Gherkin feature file syntax and ensure the steps match the capabilities of the API and Browser agents.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any bugs, feature requests, or improvements.

## License

This project is licensed under the MIT License.