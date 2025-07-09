import os
import uuid
import asyncio
from typing import Optional

# Google Cloud and ADK imports
import google.adk as adk
from google.adk.sessions import VertexAiSessionService
from google.adk.memory import VertexAiMemoryBankService
from google.adk.runners import Runner
from google.adk.types import Content, Part
from vertexai import agent_engines

# Environment configuration
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

class ADKMemoryBot:
    def __init__(self):
        self.agent_engine = None
        self.agent_engine_id = None
        self.session_service = None
        self.memory_service = None
        self.agent = None
        self.app_name = None
        self.current_session = None
        self.user_id = "user_123"
        
    async def initialize(self):
        """Initialize ADK services"""
        try:
            print("Initializing ADK Memory Bot...")
            
            # Create Agent Engine
            self.agent_engine = agent_engines.create()
            self.agent_engine_id = self.agent_engine.name
            print(f"Agent Engine created: {self.agent_engine_id}")
            
            # Initialize services
            self.session_service = VertexAiSessionService(
                project=PROJECT_ID,
                location=LOCATION,
                agent_engine_id=self.agent_engine_id
            )
            
            self.memory_service = VertexAiMemoryBankService(
                project=PROJECT_ID,
                location=LOCATION,
                agent_engine_id=self.agent_engine_id
            )
            
            # Create ADK Agent with memory capabilities
            self.agent = adk.Agent(
                model="gemini-2.0-flash-exp",
                name="memory_assistant",
                instruction="""You are a helpful assistant with perfect memory across conversations.

Instructions:
- Use the PreloadMemoryTool to access relevant context from previous conversations
- Naturally reference past conversations when relevant to provide personalized responses
- Build upon previous knowledge about the user to create continuity
- The memories shown are the most relevant to the current query based on semantic search
- Always maintain a friendly and helpful tone
- If you don't find relevant memories, focus on the current conversation""",
                tools=[adk.tools.preload_memory_tool.PreloadMemoryTool()],
            )
            
            self.app_name = f"adk_memory_bot_{uuid.uuid4().hex[:8]}"
            
            # Create initial session
            self.current_session = await self.session_service.create_session(
                app_name=self.app_name,
                user_id=self.user_id
            )
            
            print(f"✓ ADK Memory Bot initialized successfully!")
            print(f"  App: {self.app_name}")
            print(f"  Session: {self.current_session.id}")
            print(f"  User: {self.user_id}")
            
        except Exception as e:
            print(f"Error initializing ADK services: {e}")
            raise
            
    async def call_agent(self, query: str) -> str:
        """Execute agent conversation turn"""
        try:
            runner = Runner(
                agent=self.agent,
                app_name=self.app_name,
                session_service=self.session_service,
                memory_service=self.memory_service,
            )
            
            content = Content(role='user', parts=[Part(text=query)])
            final_response_text = "Agent did not produce a final response."
            
            async for event in runner.run_async(
                user_id=self.user_id,
                session_id=self.current_session.id,
                new_message=content
            ):
                if event.is_final_response():
                    if event.content and event.content.parts:
                        final_response_text = event.content.parts[0].text
                    break
            
            return final_response_text
            
        except Exception as e:
            print(f"Error in agent call: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
            
    async def save_session_to_memory(self):
        """Save current session to long-term memory"""
        try:
            # Get session from VertexAiSessionService
            completed_session = await self.session_service.get_session(
                app_name=self.app_name,
                user_id=self.user_id,
                session_id=self.current_session.id
            )
            
            # Transfer to Vertex AI Memory Bank
            await self.memory_service.add_session_to_memory(completed_session)
            print(f"✓ Session {self.current_session.id} saved to memory bank")
            
        except Exception as e:
            print(f"Error saving session to memory: {e}")
            
    async def new_session(self):
        """Create a new session (simulating new conversation)"""
        try:
            self.current_session = await self.session_service.create_session(
                app_name=self.app_name,
                user_id=self.user_id
            )
            print(f"✓ New session created: {self.current_session.id}")
            
        except Exception as e:
            print(f"Error creating new session: {e}")
            
    async def cleanup(self):
        """Cleanup resources"""
        if self.agent_engine:
            try:
                self.agent_engine.delete()
                print("✓ Agent engine cleaned up")
            except Exception as e:
                print(f"Error cleaning up agent engine: {e}")
                
    async def run_chat_loop(self):
        """Interactive chat loop"""
        print("\n" + "="*60)
        print("🤖 ADK Memory Bot - Interactive Chat")
        print("="*60)
        print("Commands:")
        print("  /new     - Start new session")
        print("  /save    - Save current session to memory")
        print("  /quit    - Exit chat")
        print("  /help    - Show this help")
        print("="*60)
        
        while True:
            try:
                user_input = input(f"\n[{self.current_session.id[:8]}] You: ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() == '/quit':
                    print("Goodbye! 👋")
                    break
                elif user_input.lower() == '/help':
                    print("\nCommands:")
                    print("  /new     - Start new session")
                    print("  /save    - Save current session to memory")
                    print("  /quit    - Exit chat")
                    print("  /help    - Show this help")
                    continue
                elif user_input.lower() == '/new':
                    await self.new_session()
                    continue
                elif user_input.lower() == '/save':
                    await self.save_session_to_memory()
                    continue
                
                # Get response from agent
                print("Bot: ", end="", flush=True)
                response = await self.call_agent(user_input)
                print(response)
                
            except KeyboardInterrupt:
                print("\nGoodbye! 👋")
                break
            except Exception as e:
                print(f"Error: {e}")

async def main():
    """Main function"""
    bot = ADKMemoryBot()
    
    try:
        await bot.initialize()
        await bot.run_chat_loop()
        
    except Exception as e:
        print(f"Fatal error: {e}")
        
    finally:
        await bot.cleanup()

if __name__ == "__main__":
    asyncio.run(main())