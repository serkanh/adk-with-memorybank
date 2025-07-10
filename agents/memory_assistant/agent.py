import google.adk as adk
import os
import asyncio
from google.adk.memory import VertexAiMemoryBankService
from google.adk.sessions import VertexAiSessionService

async def auto_save_to_memory_callback(callback_context):
    """Automatically save completed sessions to memory bank"""
    try:
        print(f"🔄 Auto-saving session to memory...")
        
        # Extract session information from callback context
        session_id = None
        user_id = None
        app_name = None
        
        # Check _invocation_context for session information
        if hasattr(callback_context, '_invocation_context'):
            inv_ctx = callback_context._invocation_context
            
            # Extract session ID from _invocation_context.session.id
            if hasattr(inv_ctx, 'session') and hasattr(inv_ctx.session, 'id'):
                session_id = inv_ctx.session.id
                print(f"🎯 Found session ID: {session_id}")
                
            # Extract user_id from _invocation_context.user_id  
            if hasattr(inv_ctx, 'user_id'):
                user_id = inv_ctx.user_id
                print(f"🎯 Found user_id: {user_id}")
                
            # Extract app_name from _invocation_context.session.app_name
            if hasattr(inv_ctx, 'session') and hasattr(inv_ctx.session, 'app_name'):
                app_name = inv_ctx.session.app_name
                print(f"🎯 Found app_name: {app_name}")
                    
        # Fallback to environment variables if not found in context
        if not user_id:
            user_id = os.getenv("DEFAULT_USER_ID", "user_123")
            
        if not app_name:
            app_name = os.getenv("APP_NAME", "adk-memory-bot")
        
        print(f"🎯 Extracted - Session ID: {session_id}, User ID: {user_id}, App Name: {app_name}")
        
        if not session_id:
            print("⚠️  No session ID found in callback context, skipping memory save")
            return
        
        # Initialize services
        agent_engine_id = os.getenv("AGENT_ENGINE_ID")
        if not agent_engine_id:
            print("⚠️  AGENT_ENGINE_ID not set, cannot save to memory")
            return
            
        session_service = VertexAiSessionService(
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
            agent_engine_id=agent_engine_id
        )
        
        memory_service = VertexAiMemoryBankService(
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
            agent_engine_id=agent_engine_id
        )
        
        # Get the session from the invocation context directly (has current events)
        session = callback_context._invocation_context.session
        
        # Check if session has meaningful content
        print(f"🔍 Session contents check from invocation context:")
        print(f"  - hasattr(session, 'contents'): {hasattr(session, 'contents')}")
        if hasattr(session, 'contents'):
            print(f"  - session.contents: {session.contents}")
            print(f"  - len(session.contents): {len(session.contents) if session.contents else 0}")
        
        # Check if session has events instead of contents
        if hasattr(session, 'events'):
            print(f"  - hasattr(session, 'events'): {hasattr(session, 'events')}")
            print(f"  - session.events: {session.events}")
            print(f"  - len(session.events): {len(session.events) if session.events else 0}")
        
        # More flexible check - look for events or contents
        has_content = False
        content_count = 0
        
        if hasattr(session, 'events') and session.events:
            content_count = len(session.events)
            has_content = content_count >= 2
        elif hasattr(session, 'contents') and session.contents:
            content_count = len(session.contents)
            has_content = content_count >= 2
            
        print(f"  - Content count: {content_count}, Has meaningful content: {has_content}")
        
        if not has_content:
            print("📭 Session has no meaningful content, skipping memory save")
            return
            
        # Transfer to memory bank
        await memory_service.add_session_to_memory(session)
        print(f"✅ Session {session_id} automatically saved to memory bank")
        
    except Exception as e:
        print(f"❌ Error auto-saving to memory: {e}")
        import traceback
        traceback.print_exc()

root_agent = adk.Agent(
    name="memory_assistant",
    model="gemini-2.0-flash-exp",
    instruction="""You are a helpful assistant with perfect memory across conversations.

Instructions:
- Use the PreloadMemoryTool to access relevant context from previous conversations
- Naturally reference past conversations when relevant to provide personalized responses
- Build upon previous knowledge about the user to create continuity
- The memories shown are the most relevant to the current query based on semantic search
- Always maintain a friendly and helpful tone
- If you don't find relevant memories, focus on the current conversation
- Keep responses concise and focused on the user's needs
- When referencing memories, do so naturally without explicitly mentioning "memory search"

Your goal is to provide consistent, personalized assistance by leveraging conversation history.

Remember: Use the PreloadMemoryTool to search for relevant information from previous conversations.""",
    tools=[adk.tools.preload_memory_tool.PreloadMemoryTool()],
    after_agent_callback=auto_save_to_memory_callback,
)
