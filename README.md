# ADK Memory Bot with Vertex AI Integration

A conversational AI agent built with Google's Agent Development Kit (ADK) that maintains persistent memory across conversations using Vertex AI Memory Bank.

## Features

- **Persistent Memory**: Conversations are stored in Vertex AI Memory Bank for long-term recall
- **Multiple Interfaces**: Web UI and API server modes via standard ADK commands
- **Session Management**: Automatic session creation and management
- **Memory Search**: Semantic search across conversation history
- **Google Cloud Integration**: Built on Vertex AI and Google Cloud Platform
- **Dockerized Deployment**: Easy container-based deployment

## Architecture

```
adk-with-memorybank/
├── agents/
│   └── memory_assistant/
│       ├── __init__.py          # Agent module imports
│       └── agent.py             # Main agent definition with PreloadMemoryTool
├── .env                         # Environment configuration
├── requirements.txt             # Python dependencies
├── docker-compose.yml           # Container orchestration
└── Dockerfile                   # Container build instructions
```

## Prerequisites

1. **Google Cloud Project** with Vertex AI enabled
2. **Google Cloud CLI** installed and configured
3. **Authentication** set up (ADC or service account)
4. **Python 3.11+** installed (for local development)
5. **Docker & Docker Compose** (for containerized deployment)
6. **Required permissions** for Vertex AI and Agent Engine

## Google Cloud Setup

### 1. Install Google Cloud CLI

**macOS:**
```bash
# Using Homebrew
brew install google-cloud-sdk

# Using installer
curl https://sdk.cloud.google.com | bash
```

**Linux:**
```bash
# Using snap
sudo snap install google-cloud-cli --classic

# Using installer
curl https://sdk.cloud.google.com | bash
```

**Windows:**
Download the installer from [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)

### 2. Initialize and Authenticate

```bash
# Initialize gcloud CLI
gcloud init

# This will:
# - Log you into Google Cloud
# - Set your default project
# - Configure your default compute region/zone

# Verify authentication
gcloud auth list
gcloud config list project
```

### 3. Application Default Credentials (ADC)

**Why use ADC?**
- **Security**: No need to manage service account keys manually
- **Convenience**: Works seamlessly with Google Cloud libraries
- **Best Practice**: Recommended authentication method for development
- **Automatic**: Libraries automatically discover and use credentials

**Set up ADC:**
```bash
# Create Application Default Credentials
gcloud auth application-default login

# This creates credentials at:
# - Linux/macOS: ~/.config/gcloud/application_default_credentials.json
# - Windows: %APPDATA%\gcloud\application_default_credentials.json
```

**Verify ADC setup:**
```bash
# Test ADC
gcloud auth application-default print-access-token

# Should return an access token
```

### 4. Enable Required APIs

```bash
# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com

# Enable other required APIs
gcloud services enable compute.googleapis.com
gcloud services enable storage.googleapis.com
```

## Installation

### Option 1: Docker Deployment (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd adk-with-memorybank
```

2. Set up environment variables:
```bash
# Set your Google Cloud project
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_CLOUD_LOCATION=us-central1
export GOOGLE_GENAI_USE_VERTEXAI=TRUE
```

3. **Create Agent Engine** (Required):
```bash
# Create the Agent Engine first
docker-compose run --rm memory-bot-web python create_agent_engine.py

# This will:
# 1. Create a new Agent Engine in Google Cloud
# 2. Update your .env file with the AGENT_ENGINE_ID
# 3. Show you the Agent Engine details
```

4. **Choose Authentication Method:**

#### Option A: Use Application Default Credentials (Recommended)
```bash
# Set up ADC (see Google Cloud Setup section above)
gcloud auth application-default login

# Update docker-compose.yml to mount ADC
# (see Docker Credential Mounting section below)
```

#### Option B: Use Service Account Key
```bash
# Create service account
gcloud iam service-accounts create adk-memory-bot \
  --display-name="ADK Memory Bot Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:adk-memory-bot@your-project-id.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# Create and download key
gcloud iam service-accounts keys create credentials/service-account.json \
  --iam-account=adk-memory-bot@your-project-id.iam.gserviceaccount.com

# Create credentials directory
mkdir -p credentials
```

5. Start the services:
```bash
# Start web interface
docker-compose up memory-bot-web

# OR start API server
docker-compose up memory-bot-api

# OR start both
docker-compose up
```

**Expected Output:**
When successful, you should see:
```
ADK Web Server started

For local testing, access at http://localhost:8000.
```

## Docker Credential Mounting

### Method 1: Application Default Credentials (Recommended)

Update your `docker-compose.yml` to mount ADC:

```yaml
services:
  memory-bot-web:
    # ... other configuration
    volumes:
      - ~/.config/gcloud:/root/.config/gcloud:ro  # Mount ADC
      - ./logs:/app/logs
    environment:
      # Remove GOOGLE_APPLICATION_CREDENTIALS if using ADC
      GOOGLE_CLOUD_PROJECT: ${GOOGLE_CLOUD_PROJECT}
      GOOGLE_CLOUD_LOCATION: ${GOOGLE_CLOUD_LOCATION}
      GOOGLE_GENAI_USE_VERTEXAI: "TRUE"
```

**For different operating systems:**

**Linux/macOS:**
```yaml
volumes:
  - ~/.config/gcloud:/root/.config/gcloud:ro
```

**Windows:**
```yaml
volumes:
  - %APPDATA%\gcloud:/root/.config/gcloud:ro
```

### Method 2: Service Account Key

Keep the existing configuration:
```yaml
services:
  memory-bot-web:
    # ... other configuration
    volumes:
      - ./credentials:/app/credentials:ro
      - ./logs:/app/logs
    environment:
      GOOGLE_APPLICATION_CREDENTIALS: /app/credentials/service-account.json
```

### Method 3: Environment Variable Key (Not Recommended)

For CI/CD or when file mounting is not possible:
```yaml
services:
  memory-bot-web:
    # ... other configuration
    environment:
      GOOGLE_APPLICATION_CREDENTIALS_JSON: ${GOOGLE_SERVICE_ACCOUNT_KEY_JSON}
```

### Verification

Test your Docker authentication:
```bash
# Test with ADC
docker-compose run memory-bot-web gcloud auth application-default print-access-token

# Test with service account
docker-compose run memory-bot-web gcloud auth activate-service-account --key-file=/app/credentials/service-account.json
```

### Quick Test

Verify the agent structure is correct:
```bash
# Test that ADK can find the agents directory
docker-compose run --rm memory-bot-web ls -la /app/agents/

# Should show: memory_assistant directory

# Test agent loading
docker-compose run --rm memory-bot-web python -c "
import sys
sys.path.append('/app/agents')
from memory_assistant import root_agent
print('Agent loaded successfully:', root_agent.name)
"
```

### Option 2: Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_CLOUD_LOCATION=us-central1
export GOOGLE_GENAI_USE_VERTEXAI=TRUE
```

3. Run ADK commands:
```bash
# Web interface (specify agents directory)
adk web agents

# API server (specify agents directory)
adk api_server agents

# CLI interface (specify specific agent)
adk run agents/memory_assistant
```

## Usage

### Docker Deployment

The application is designed to be run with standard ADK commands in Docker containers:

**Web Interface:**
```bash
# Start web interface container
docker-compose up memory-bot-web
```
- Access at: http://localhost:8000
- Interactive browser-based chat interface
- Real-time conversation with memory recall
- Session management controls

**API Server:**
```bash
# Start API server container
docker-compose up memory-bot-api
```
- API available at: http://localhost:8001
- RESTful API for programmatic access
- Same memory capabilities as web interface

**Both Services:**
```bash
# Start both web and API
docker-compose up
```
- Web UI: http://localhost:8000
- API: http://localhost:8001

### API Endpoints

When running the API server, the following endpoints are available:

#### Test with cURL:

**Chat with the agent:**
```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, remember that I like pizza"}'
```

**Check health:**
```bash
curl http://localhost:8001/health
```

### Environment Configuration

Required environment variables in `.env`:

```env
# Google Cloud / Vertex AI Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=TRUE

# ADK Configuration
APP_NAME=adk-memory-bot
DEFAULT_USER_ID=user_123
```

## How It Works

### Memory Architecture
1. **Agent Engine**: Single Vertex AI Agent Engine manages both session and memory services
2. **Session Service**: Active conversation state with VertexAiSessionService
3. **Memory Bank Service**: Long-term storage with VertexAiMemoryBankService
4. **PreloadMemoryTool**: Built-in tool for automatic memory access

### Conversation Flow
1. User sends message → Agent receives input
2. PreloadMemoryTool automatically searches relevant memories
3. Agent responds with both session context and memory context
4. New conversation data stored in session service
5. Completed sessions can be transferred to memory bank for long-term storage

### Agent Configuration

The agent (`agents/memory_assistant/agent.py`) includes:

- **Model**: gemini-2.0-flash-exp
- **Tools**: PreloadMemoryTool for automatic memory access
- **Instructions**: Specialized prompts for memory-aware conversations
- **Memory Integration**: Seamless access to conversation history

## Development

### Project Structure

The project follows Google ADK conventions:

- `agents/memory_assistant/`: Standard ADK agent directory
- `agents/memory_assistant/__init__.py`: Imports root_agent
- `agents/memory_assistant/agent.py`: Agent definition with memory tools
- Standard ADK commands work: `adk web`, `adk api_server`, `adk run`

### Extending the Agent

1. **Add new tools** to `agents/memory_assistant/agent.py`:
```python
from google.adk.tools import FunctionTool

def my_custom_tool():
    """Custom tool description"""
    return "tool result"

root_agent = adk.Agent(
    name="memory_assistant",
    model="gemini-2.0-flash-exp",
    tools=[
        adk.tools.preload_memory_tool.PreloadMemoryTool(),
        FunctionTool(my_custom_tool)
    ]
)
```

2. **Modify agent instructions** for new behaviors
3. **Update Docker environment** as needed

### Testing

Test the agent locally:
```bash
# Quick test with CLI (specify full agent path)
adk run agents/memory_assistant

# Test web interface (specify agents directory)
adk web agents
# Visit http://localhost:8000

# Test API server (specify agents directory)
adk api_server agents
# API at http://localhost:8000
```

## Deployment

### Docker Compose Services

The `docker-compose.yml` defines two services:

1. **memory-bot-web**: Web interface on port 8000
2. **memory-bot-api**: API server on port 8001

Both services:
- Use the same Docker image with ADK installed
- Mount Google Cloud credentials
- Use standard ADK commands (`adk web`, `adk api_server`)
- Share the same agent code

### Production Considerations

1. **Authentication**: Use service account keys or Workload Identity
2. **Scaling**: Run multiple API instances behind load balancer
3. **Monitoring**: Add health checks and logging
4. **Security**: Secure credential management and network policies

## Troubleshooting

### Common Issues

**"Directory 'memory_assistant' does not exist" Error:**
This means the ADK command path is incorrect. The correct format is:
```bash
# Correct: Specify agents directory (contains all agent subdirectories)
adk web agents

# Incorrect: Specify individual agent
adk web memory_assistant
```

**"No root_agent found" Error:**
Check agent structure:
```bash
# Verify agent structure
ls -la agents/memory_assistant/
# Should show: __init__.py and agent.py

# Check __init__.py content
cat agents/memory_assistant/__init__.py
# Should contain: from .agent import root_agent
```

**ADK Command Not Found:**
```bash
# Ensure ADK is installed
pip install google-adk>=1.5.0

# Check installation
adk --help
```

**Authentication Error:**
```bash
# Check service account key
ls -la credentials/service-account.json

# Verify environment variables
echo $GOOGLE_CLOUD_PROJECT

# Test ADC
gcloud auth application-default print-access-token
```

**Memory Bank Access:**
```bash
# Verify Vertex AI is enabled
gcloud services list --enabled | grep aiplatform

# Check IAM permissions
gcloud auth list
```

**Docker Issues:**
```bash
# Rebuild images
docker-compose build --no-cache

# Check logs
docker-compose logs memory-bot-web
docker-compose logs memory-bot-api

# Test container structure
docker-compose run --rm memory-bot-web ls -la /app/agents/
```

### Debug Mode

Enable debug logging:
```bash
# In .env file
GOOGLE_CLOUD_LOG_LEVEL=DEBUG

# Or export environment variable
export GOOGLE_CLOUD_LOG_LEVEL=DEBUG
```

## Monitoring Sessions and Memory

### Check Sessions and Memory Entries

Use the included utility script to inspect your ADK sessions and memory:

```bash
# Run from Docker container
docker-compose run --rm memory-bot-web python check_sessions_memory.py

# Or run locally (after setting environment variables)
python check_sessions_memory.py
```

### Google Cloud Console

1. **Agent Engine Dashboard**:
   - Navigate to: Google Cloud Console → AI Platform → Agent Engine
   - Find your Agent Engine ID in the application logs
   - View Sessions and Memory tabs

2. **Using gcloud CLI**:
```bash
# List sessions
gcloud ai agent-engines sessions list \
  --agent-engine=YOUR_AGENT_ENGINE_ID \
  --location=us-central1

# List memory entries
gcloud ai agent-engines memory-entries list \
  --agent-engine=YOUR_AGENT_ENGINE_ID \
  --location=us-central1
```

### Get Agent Engine ID

```bash
# From Docker logs
docker-compose logs memory-bot-web | grep -i "agent engine"

# Or from gcloud
gcloud ai agent-engines list --location=us-central1
```

## License

This project is licensed under the MIT License.

## Acknowledgments

- Google Agent Development Kit (ADK) team
- Vertex AI and Google Cloud Platform
- Open source community contributions