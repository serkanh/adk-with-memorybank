#!/usr/bin/env python3
"""
Utility script to check ADK sessions and memory entries in Google Cloud
"""

import asyncio
import os
import sys
from datetime import datetime

# Add agents to path
sys.path.append('/app/agents')

from google.adk.sessions import VertexAiSessionService
from google.adk.memory import VertexAiMemoryBankService
from vertexai import agent_engines

# Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
APP_NAME = os.getenv("APP_NAME", "adk-memory-bot")
USER_ID = os.getenv("DEFAULT_USER_ID", "user_123")

async def get_agent_engine_id():
    """Get the Agent Engine ID"""
    try:
        # Try to create/get agent engine
        agent_engine = agent_engines.create()
        return agent_engine.name
    except Exception as e:
        print(f"Error getting agent engine: {e}")
        return None

async def check_sessions(agent_engine_id):
    """Check sessions for the agent"""
    print("\n" + "="*50)
    print("📝 CHECKING SESSIONS")
    print("="*50)
    
    try:
        session_service = VertexAiSessionService(
            project=PROJECT_ID,
            location=LOCATION,
            agent_engine_id=agent_engine_id
        )
        
        # List sessions for the user
        sessions_response = await session_service.list_sessions(
            app_name=APP_NAME,
            user_id=USER_ID
        )
        
        # Extract actual sessions list
        sessions = []
        if hasattr(sessions_response, 'sessions'):
            sessions = sessions_response.sessions or []
        elif hasattr(sessions_response, 'items'):
            sessions = sessions_response.items or []
        else:
            try:
                sessions = list(sessions_response)
            except:
                sessions = []
        
        if not sessions:
            print("No sessions found.")
            return
            
        print(f"Found {len(sessions)} sessions:")
        
        for i, session in enumerate(sessions, 1):
            print(f"\n{i}. Session ID: {session.id}")
            print(f"   Created: {session.created_time}")
            print(f"   Status: {getattr(session, 'status', 'N/A')}")
            print(f"   App: {getattr(session, 'app_name', 'N/A')}")
            print(f"   User: {getattr(session, 'user_id', 'N/A')}")
            
            # Get session details
            try:
                session_detail = await session_service.get_session(
                    app_name=APP_NAME,
                    user_id=USER_ID,
                    session_id=session.id
                )
                
                if hasattr(session_detail, 'contents') and session_detail.contents:
                    print(f"   Messages: {len(session_detail.contents)}")
                    
                    # Show last few messages
                    for j, content in enumerate(session_detail.contents[-3:], 1):
                        role = getattr(content, 'role', 'unknown')
                        parts = getattr(content, 'parts', [])
                        if parts:
                            text = getattr(parts[0], 'text', '')[:100] + "..." if len(getattr(parts[0], 'text', '')) > 100 else getattr(parts[0], 'text', '')
                            print(f"     {role}: {text}")
                            
            except Exception as e:
                print(f"   Error getting session details: {e}")
                
    except Exception as e:
        print(f"Error checking sessions: {e}")

async def check_memory(agent_engine_id):
    """Check memory entries for the agent"""
    print("\n" + "="*50)
    print("🧠 CHECKING MEMORY BANK")
    print("="*50)
    
    try:
        memory_service = VertexAiMemoryBankService(
            project=PROJECT_ID,
            location=LOCATION,
            agent_engine_id=agent_engine_id
        )
        
        # Search memories (empty query to get all)
        try:
            memories = await memory_service.search_memory(
                user_id=USER_ID,
                query="",
                limit=20
            )
            
            if not memories:
                print("No memories found.")
                return
                
            print(f"Found {len(memories)} memories:")
            
            for i, memory in enumerate(memories, 1):
                print(f"\n{i}. Memory ID: {getattr(memory, 'id', 'N/A')}")
                print(f"   Created: {getattr(memory, 'created_time', 'N/A')}")
                print(f"   User: {getattr(memory, 'user_id', 'N/A')}")
                
                # Show content preview
                content = getattr(memory, 'content', '')
                if content:
                    preview = content[:200] + "..." if len(content) > 200 else content
                    print(f"   Content: {preview}")
                    
        except Exception as e:
            print(f"Error searching memories: {e}")
            # Try alternative approach
            print("Trying alternative memory listing...")
            
    except Exception as e:
        print(f"Error checking memory: {e}")

async def main():
    """Main function"""
    print("🔍 ADK Sessions and Memory Checker")
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print(f"App: {APP_NAME}")
    print(f"User: {USER_ID}")
    
    # Get agent engine ID
    agent_engine_id = await get_agent_engine_id()
    if not agent_engine_id:
        print("❌ Could not get Agent Engine ID")
        return
        
    print(f"Agent Engine ID: {agent_engine_id}")
    
    # Check sessions
    await check_sessions(agent_engine_id)
    
    # Check memory
    await check_memory(agent_engine_id)
    
    print("\n" + "="*50)
    print("✅ Checking complete!")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())
