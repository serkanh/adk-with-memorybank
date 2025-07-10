#!/usr/bin/env python3
"""
Test script to diagnose session service issues
"""

import asyncio
import os
import sys
from google.adk.sessions import VertexAiSessionService

# Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
AGENT_ENGINE_ID = os.getenv("AGENT_ENGINE_ID")
APP_NAME = os.getenv("APP_NAME", "adk-memory-bot")
USER_ID = os.getenv("DEFAULT_USER_ID", "user_123")

async def test_session_service():
    """Test the session service configuration"""
    print("🧪 Testing Session Service Configuration")
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print(f"Agent Engine ID: {AGENT_ENGINE_ID}")
    print(f"App Name: {APP_NAME}")
    print(f"User ID: {USER_ID}")
    
    if not AGENT_ENGINE_ID:
        print("❌ AGENT_ENGINE_ID is not set!")
        return
    
    try:
        # Initialize session service
        session_service = VertexAiSessionService(
            project=PROJECT_ID,
            location=LOCATION,
            agent_engine_id=AGENT_ENGINE_ID
        )
        print("✅ Session service initialized successfully")
        
        # Try to list sessions
        print("\n📋 Listing existing sessions...")
        sessions_response = await session_service.list_sessions(
            app_name=APP_NAME,
            user_id=USER_ID
        )
        print(f"Sessions response type: {type(sessions_response)}")
        print(f"Sessions response attributes: {dir(sessions_response)}")
        
        # Extract the actual sessions list
        sessions = []
        if hasattr(sessions_response, 'sessions'):
            sessions = sessions_response.sessions
        elif hasattr(sessions_response, 'items'):
            sessions = sessions_response.items
        else:
            # Try to iterate directly
            try:
                sessions = list(sessions_response)
            except:
                sessions = []
        
        print(f"Found {len(sessions)} sessions:")
        
        for i, session in enumerate(sessions, 1):
            print(f"  {i}. Session ID: {session.id}")
            print(f"     Created: {session.created_time}")
            print(f"     Type: {type(session)}")
            print(f"     Dir: {dir(session)}")
            
            # Try to get session details (this is where the error occurs)
            try:
                print(f"\n🔍 Testing get_session for session {session.id}...")
                session_detail = await session_service.get_session(
                    app_name=APP_NAME,
                    user_id=USER_ID,
                    session_id=session.id
                )
                print(f"✅ Successfully retrieved session details")
                print(f"   Session has {len(getattr(session_detail, 'contents', []))} contents")
                
            except Exception as e:
                print(f"❌ Error getting session details: {e}")
                import traceback
                traceback.print_exc()
                
        # Try to create a new session
        print(f"\n🆕 Testing session creation...")
        try:
            new_session = await session_service.create_session(
                app_name=APP_NAME,
                user_id=USER_ID
            )
            print(f"✅ Successfully created new session: {new_session.id}")
            
            # Try to get the new session immediately
            try:
                print(f"🔍 Testing get_session for new session {new_session.id}...")
                new_session_detail = await session_service.get_session(
                    app_name=APP_NAME,
                    user_id=USER_ID,
                    session_id=new_session.id
                )
                print(f"✅ Successfully retrieved new session details")
                
            except Exception as e:
                print(f"❌ Error getting new session details: {e}")
                import traceback
                traceback.print_exc()
                
        except Exception as e:
            print(f"❌ Error creating session: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Error initializing session service: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_session_service()) 
