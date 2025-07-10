#!/usr/bin/env python3
"""
Simple script to save recent sessions to memory bank
Run this periodically or after conversations to ensure memory persistence
"""

import asyncio
import os
from google.adk.sessions import VertexAiSessionService
from google.adk.memory import VertexAiMemoryBankService
from dotenv import load_dotenv

load_dotenv()

async def save_recent_sessions():
    """Save recent sessions to memory bank"""
    
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
    
    app_name = os.getenv("APP_NAME", "adk-memory-bot")
    
    try:
        # List recent sessions for the default user
        sessions_response = await session_service.list_sessions(
            app_name=app_name,
            user_id="user"  # Default user from web interface
        )
        
        sessions = list(sessions_response.sessions)
        print(f"📋 Found {len(sessions)} total sessions")
        
        saved_count = 0
        for session in sessions:
            try:
                print(f"🔄 Processing session: {session.id}")
                
                # Get session details - this might fail with 500 errors
                # but let's try a simpler approach
                await memory_service.add_session_to_memory(session)
                print(f"✅ Saved session {session.id} to memory bank")
                saved_count += 1
                
            except Exception as e:
                print(f"⚠️  Could not save session {session.id}: {e}")
                continue
        
        print(f"🎉 Successfully saved {saved_count} sessions to memory bank")
        
        # Test memory search
        print("🔍 Testing memory search...")
        results = await memory_service.search_memory(
            app_name=app_name,
            user_id="user",
            query="burger"
        )
        
        print(f"💭 Found {len(results.memories)} memories about 'burger'")
        for i, memory in enumerate(results.memories[:3], 1):
            print(f"  {i}. {memory}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(save_recent_sessions())