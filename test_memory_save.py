#!/usr/bin/env python3
"""
Test script to manually save a session to memory bank
"""

import asyncio
import os
from google.adk.sessions import VertexAiSessionService
from google.adk.memory import VertexAiMemoryBankService
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

async def main():
    # Initialize services
    session_service = VertexAiSessionService(
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        agent_engine_id=os.getenv("AGENT_ENGINE_ID")
    )
    
    memory_service = VertexAiMemoryBankService(
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        agent_engine_id=os.getenv("AGENT_ENGINE_ID")
    )
    
    # Create a test session
    print("Creating test session...")
    session = await session_service.create_session(
        app_name="test-app",
        user_id="test-user"
    )
    
    print(f"Created session: {session.id}")
    
    # Add some test events
    user_content = types.Content(
        role="user",
        parts=[types.Part(text="I love pizza and Italian food")]
    )
    
    assistant_content = types.Content(
        role="assistant", 
        parts=[types.Part(text="That's great! Pizza is delicious. Do you have a favorite topping?")]
    )
    
    # Create events
    from google.adk.sessions.models import Event
    
    user_event = Event(
        content=user_content,
        invocation_id="test-1",
        author="user"
    )
    
    assistant_event = Event(
        content=assistant_content,
        invocation_id="test-2", 
        author="assistant"
    )
    
    # Add events to session
    await session_service.append_event(session, user_event)
    await session_service.append_event(session, assistant_event)
    
    print("Added test events to session")
    
    # Get the updated session
    updated_session = await session_service.get_session(
        app_name="test-app",
        user_id="test-user",
        session_id=session.id
    )
    
    print(f"Session type: {type(updated_session)}")
    print(f"Session attributes: {[attr for attr in dir(updated_session) if not attr.startswith('_')]}")
    
    # Try to save to memory
    print("Saving to memory bank...")
    try:
        await memory_service.add_session_to_memory(updated_session)
        print("✅ Successfully saved to memory bank!")
    except Exception as e:
        print(f"❌ Error saving to memory: {e}")
    
    # Test search
    print("Searching memory...")
    try:
        results = await memory_service.search_memory(
            app_name="test-app",
            user_id="test-user",
            query="pizza"
        )
        print(f"Found {len(results.memories)} memories about pizza")
        for i, memory in enumerate(results.memories, 1):
            print(f"{i}. {memory}")
    except Exception as e:
        print(f"❌ Error searching memory: {e}")

if __name__ == "__main__":
    asyncio.run(main())