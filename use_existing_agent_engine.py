"""
Example: Using an existing Agent Engine instead of creating one automatically
"""

import os
from google.adk.sessions import VertexAiSessionService
from google.adk.memory import VertexAiMemoryBankService

# If you manually created an Agent Engine, use its ID directly
EXISTING_AGENT_ENGINE_ID = "projects/your-project/locations/us-central1/agentEngines/12345"

# Or get it from environment variable
AGENT_ENGINE_ID = os.getenv("AGENT_ENGINE_ID", EXISTING_AGENT_ENGINE_ID)

# Initialize services with existing Agent Engine
session_service = VertexAiSessionService(
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
    agent_engine_id=AGENT_ENGINE_ID  # Use existing instead of creating
)

memory_service = VertexAiMemoryBankService(
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
    agent_engine_id=AGENT_ENGINE_ID  # Use existing instead of creating
)

print(f"Using existing Agent Engine: {AGENT_ENGINE_ID}")