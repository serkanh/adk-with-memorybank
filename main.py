#!/usr/bin/env python3
"""
Main application with ADK Runner, Session Service, and Memory Bank integration
"""

import asyncio
import os
import sys
from typing import Optional
import uuid

# Add agents to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))

from google.adk import Runner
from google.adk.sessions import VertexAiSessionService
from google.adk.memory import VertexAiMemoryBankService
from google.genai import types
from vertexai import agent_engines
from dotenv import load_dotenv

# Import our agent
from memory_assistant.agent import root_agent

# Load environment variables
load_dotenv()

# Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
AGENT_ENGINE_ID = os.getenv("AGENT_ENGINE_ID")
APP_NAME = os.getenv("APP_NAME", "adk-memory-bot")
DEFAULT_USER_ID = os.getenv("DEFAULT_USER_ID", "user_123")

# Set Vertex AI environment
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"


class MemoryBotApplication:
    """Main application class for the ADK Memory Bot"""

    def __init__(self):
        self.project_id = PROJECT_ID
        self.location = LOCATION
        self.agent_engine_id = AGENT_ENGINE_ID
        self.app_name = APP_NAME
        self.session_service = None
        self.memory_service = None
        self.runner = None

    async def initialize(self):
        """Initialize services and runner"""
        print("🚀 Initializing ADK Memory Bot...")

        # Get or create agent engine ID if not provided
        if not self.agent_engine_id:
            print("Creating new Agent Engine...")
            agent_engine = agent_engines.create()
            self.agent_engine_id = agent_engine.name.split("/")[-1]
            print(f"Created Agent Engine: {self.agent_engine_id}")
        else:
            print(f"Using existing Agent Engine: {self.agent_engine_id}")

        # Initialize Session Service
        print("Initializing Session Service...")
        self.session_service = VertexAiSessionService(
            project=self.project_id,
            location=self.location,
            agent_engine_id=self.agent_engine_id
        )

        # Initialize Memory Bank Service
        print("Initializing Memory Bank Service...")
        self.memory_service = VertexAiMemoryBankService(
            project=self.project_id,
            location=self.location,
            agent_engine_id=self.agent_engine_id
        )

        # Create Runner with all services
        print("Creating Runner...")
        self.runner = Runner(
            agent=root_agent,
            app_name=self.app_name,
            session_service=self.session_service,
            memory_service=self.memory_service
        )

        print("✅ Initialization complete!")

    async def create_session(self, user_id: str, session_id: Optional[str] = None) -> str:
        """Create a new session for a user"""
        if not session_id:
            session_id = f"session_{uuid.uuid4().hex[:8]}"

        await self.session_service.create_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id,
            state={"session_started": True}
        )

        print(f"📝 Created session: {session_id} for user: {user_id}")
        return session_id

    async def run_conversation_turn(self, user_id: str, session_id: str, message: str) -> str:
        """Execute a single conversation turn"""
        # Create user message content
        content = types.Content(
            role='user',
            parts=[types.Part(text=message)]
        )

        final_response = ""

        # Run the agent and process events
        async for event in self.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response = event.content.parts[0].text
                break

        return final_response

    async def save_session_to_memory(self, user_id: str, session_id: str):
        """Save completed session to memory bank"""
        print(f"💾 Saving session {session_id} to memory bank...")

        # Get the completed session
        session = await self.session_service.get_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id
        )

        # Add to memory bank
        await self.memory_service.add_session_to_memory(session)
        print("✅ Session saved to memory bank!")

    async def search_memories(self, user_id: str, query: str, limit: int = 5):
        """Search user's memories"""
        results = await self.memory_service.search_memory(
            app_name=self.app_name,
            user_id=user_id,
            query=query,
            limit=limit
        )
        return results


async def main():
    """Run an interactive chat session"""
    app = MemoryBotApplication()
    await app.initialize()

    # Get user ID
    user_id = input(f"Enter user ID (default: {DEFAULT_USER_ID}): ").strip()
    if not user_id:
        user_id = DEFAULT_USER_ID

    # Create new session
    session_id = await app.create_session(user_id)

    print("\n🤖 ADK Memory Bot Ready!")
    print("Type 'exit' to quit, 'save' to save session to memory")
    print("Type 'search <query>' to search memories")
    print("-" * 50)

    try:
        while True:
            # Get user input
            message = input("\nYou: ").strip()

            if message.lower() == 'exit':
                break
            elif message.lower() == 'save':
                await app.save_session_to_memory(user_id, session_id)
                continue
            elif message.lower().startswith('search '):
                query = message[7:]
                print(f"\n🔍 Searching memories for: {query}")
                results = await app.search_memories(user_id, query)
                if results.memories:
                    print(f"Found {len(results.memories)} relevant memories")
                    for memory in results.memories[:3]:
                        print(f"  - {memory}")
                else:
                    print("No memories found")
                continue

            # Run conversation turn
            response = await app.run_conversation_turn(user_id, session_id, message)
            print(f"\nAssistant: {response}")

    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")

    # Ask if user wants to save session
    save = input("\nSave this session to memory? (y/n): ").strip().lower()
    if save == 'y':
        await app.save_session_to_memory(user_id, session_id)


if __name__ == "__main__":
    asyncio.run(main())