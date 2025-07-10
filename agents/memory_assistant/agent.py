import google.adk as adk

# Simple callback that logs when conversations happen
async def conversation_callback(callback_context):
    """Log conversation activity for monitoring"""
    try:
        print(f"💬 Conversation turn completed")
        
        # Just mark that a conversation happened - ADK will handle the rest
        if hasattr(callback_context, 'state'):
            callback_context.state['last_interaction'] = True
            print(f"✅ Conversation logged")
        
    except Exception as e:
        print(f"❌ Callback error: {e}")
    
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
    after_agent_callback=conversation_callback,
)