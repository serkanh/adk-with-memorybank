import google.adk as adk
import os
import asyncio
from google.adk.sessions import VertexAiSessionService
from google.adk.memory import VertexAiMemoryBankService


async def save_session_to_memory_callback(callback_context):
    """
    After agent callback that logs session info for debugging.
    We'll implement memory saving separately to avoid API issues.
    """
    try:
        # Log what's available in the callback context
        session_id = getattr(callback_context, 'session_id', 'unknown')
        user_id = getattr(callback_context, 'user_id', 'unknown')
        app_name = getattr(callback_context, 'app_name', 'unknown')
        
        print(f"🔄 Callback triggered - Session: {session_id}, User: {user_id}, App: {app_name}")
        print(f"📝 Context attributes: {[attr for attr in dir(callback_context) if not attr.startswith('_')]}")
        
        # Check if we have state access
        if hasattr(callback_context, 'state'):
            print(f"📊 Session state keys: {list(callback_context.state.keys()) if callback_context.state else 'None'}")
        
    except Exception as e:
        print(f"❌ Error in callback: {e}")
    
    # Always return None to continue normal processing
    return None


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
    after_agent_callback=save_session_to_memory_callback,
)