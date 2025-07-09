import os
import uuid
import asyncio
from typing import Optional, Dict, Any
import json
from datetime import datetime

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

class ADKWebInterface:
    def __init__(self):
        self.agent_engine = None
        self.agent_engine_id = None
        self.session_service = None
        self.memory_service = None
        self.agent = None
        self.app_name = None
        self.sessions = {}  # user_id -> session_id mapping
        
    async def initialize(self):
        """Initialize ADK services"""
        try:
            print("🌐 Initializing ADK Web Interface...")
            
            # Create Agent Engine
            self.agent_engine = agent_engines.create()
            self.agent_engine_id = self.agent_engine.name
            print(f"✓ Agent Engine created: {self.agent_engine_id}")
            
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
                name="web_memory_assistant",
                instruction="""You are a helpful web assistant with perfect memory across conversations.

Instructions:
- Use the PreloadMemoryTool to access relevant context from previous conversations
- Provide concise, web-friendly responses suitable for chat interfaces
- Reference past conversations naturally when relevant
- Build upon previous knowledge about the user
- Keep responses formatted for web display (use line breaks appropriately)
- The memories shown are the most relevant to the current query based on semantic search
- Always maintain a friendly and helpful tone""",
                tools=[adk.tools.preload_memory_tool.PreloadMemoryTool()],
            )
            
            self.app_name = f"adk_web_bot_{uuid.uuid4().hex[:8]}"
            
            print(f"✓ ADK Web Interface initialized successfully!")
            print(f"  App: {self.app_name}")
            
        except Exception as e:
            print(f"❌ Error initializing ADK services: {e}")
            raise
            
    async def get_or_create_session(self, user_id: str) -> str:
        """Get existing session or create new one for user"""
        if user_id not in self.sessions:
            session = await self.session_service.create_session(
                app_name=self.app_name,
                user_id=user_id
            )
            self.sessions[user_id] = session.id
            print(f"✓ New session created for user {user_id}: {session.id}")
        
        return self.sessions[user_id]
        
    async def chat(self, user_id: str, message: str) -> Dict[str, Any]:
        """Process chat message and return response"""
        try:
            session_id = await self.get_or_create_session(user_id)
            
            runner = Runner(
                agent=self.agent,
                app_name=self.app_name,
                session_service=self.session_service,
                memory_service=self.memory_service,
            )
            
            content = Content(role='user', parts=[Part(text=message)])
            final_response_text = "Agent did not produce a final response."
            
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content
            ):
                if event.is_final_response():
                    if event.content and event.content.parts:
                        final_response_text = event.content.parts[0].text
                    break
            
            return {
                "success": True,
                "response": final_response_text,
                "session_id": session_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "session_id": self.sessions.get(user_id, "unknown"),
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
    async def save_session_to_memory(self, user_id: str) -> Dict[str, Any]:
        """Save user's current session to memory bank"""
        try:
            if user_id not in self.sessions:
                return {
                    "success": False,
                    "error": "No active session found for user"
                }
            
            session_id = self.sessions[user_id]
            
            # Get session from VertexAiSessionService
            completed_session = await self.session_service.get_session(
                app_name=self.app_name,
                user_id=user_id,
                session_id=session_id
            )
            
            # Transfer to Vertex AI Memory Bank
            await self.memory_service.add_session_to_memory(completed_session)
            
            return {
                "success": True,
                "message": f"Session {session_id} saved to memory bank",
                "session_id": session_id,
                "user_id": user_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id
            }
            
    async def new_session(self, user_id: str) -> Dict[str, Any]:
        """Create new session for user"""
        try:
            session = await self.session_service.create_session(
                app_name=self.app_name,
                user_id=user_id
            )
            self.sessions[user_id] = session.id
            
            return {
                "success": True,
                "session_id": session.id,
                "user_id": user_id,
                "message": "New session created"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id
            }
            
    async def get_session_info(self, user_id: str) -> Dict[str, Any]:
        """Get current session information"""
        return {
            "user_id": user_id,
            "session_id": self.sessions.get(user_id, None),
            "has_session": user_id in self.sessions,
            "app_name": self.app_name
        }
        
    def generate_html_interface(self) -> str:
        """Generate HTML interface for web chat"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ADK Memory Bot - Web Interface</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            width: 90%;
            max-width: 800px;
            height: 700px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #4285f4 0%, #34a853 100%);
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 24px;
            font-weight: bold;
        }
        
        .chat-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
        }
        
        .message {
            margin-bottom: 15px;
            padding: 10px 15px;
            border-radius: 15px;
            max-width: 70%;
            word-wrap: break-word;
        }
        
        .user-message {
            background: #4285f4;
            color: white;
            margin-left: auto;
            text-align: right;
        }
        
        .bot-message {
            background: white;
            color: #333;
            border: 1px solid #e0e0e0;
            margin-right: auto;
        }
        
        .input-container {
            display: flex;
            padding: 20px;
            background: white;
            border-top: 1px solid #e0e0e0;
        }
        
        .user-input {
            flex: 1;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            margin-right: 10px;
        }
        
        .send-button {
            background: #4285f4;
            color: white;
            border: none;
            border-radius: 25px;
            padding: 12px 20px;
            cursor: pointer;
            font-size: 16px;
            transition: background 0.3s;
        }
        
        .send-button:hover {
            background: #3367d6;
        }
        
        .controls {
            display: flex;
            gap: 10px;
            padding: 15px 20px;
            background: #f8f9fa;
            border-top: 1px solid #e0e0e0;
        }
        
        .control-button {
            background: #34a853;
            color: white;
            border: none;
            border-radius: 20px;
            padding: 8px 16px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s;
        }
        
        .control-button:hover {
            background: #2d8f47;
        }
        
        .status {
            padding: 10px 20px;
            font-size: 12px;
            color: #666;
            background: #f8f9fa;
            border-top: 1px solid #e0e0e0;
        }
        
        .typing {
            font-style: italic;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            🤖 ADK Memory Bot - Web Interface
        </div>
        
        <div class="chat-container">
            <div class="messages" id="messages">
                <div class="message bot-message">
                    Hi! I'm your ADK Memory Bot. I can remember our conversations across sessions. Try asking me something!
                </div>
            </div>
            
            <div class="controls">
                <button class="control-button" onclick="newSession()">New Session</button>
                <button class="control-button" onclick="saveSession()">Save to Memory</button>
                <button class="control-button" onclick="clearChat()">Clear Chat</button>
            </div>
            
            <div class="input-container">
                <input type="text" class="user-input" id="userInput" placeholder="Type your message..." onkeypress="handleKeyPress(event)">
                <button class="send-button" onclick="sendMessage()">Send</button>
            </div>
        </div>
        
        <div class="status" id="status">
            Ready - Session: <span id="sessionId">Not created</span>
        </div>
    </div>

    <script>
        const userId = 'web_user_' + Math.random().toString(36).substr(2, 9);
        let sessionId = null;
        
        async function sendMessage() {
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message to chat
            addMessage(message, 'user');
            input.value = '';
            
            // Show typing indicator
            showTyping();
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        user_id: userId,
                        message: message
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    addMessage(data.response, 'bot');
                    sessionId = data.session_id;
                    updateStatus();
                } else {
                    addMessage(`Error: ${data.error}`, 'bot');
                }
            } catch (error) {
                addMessage(`Network error: ${error.message}`, 'bot');
            }
            
            hideTyping();
        }
        
        function addMessage(text, sender) {
            const messagesContainer = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}-message`;
            messageDiv.textContent = text;
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        function showTyping() {
            const messagesContainer = document.getElementById('messages');
            const typingDiv = document.createElement('div');
            typingDiv.className = 'message bot-message typing';
            typingDiv.id = 'typing';
            typingDiv.textContent = 'Bot is typing...';
            messagesContainer.appendChild(typingDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        function hideTyping() {
            const typing = document.getElementById('typing');
            if (typing) {
                typing.remove();
            }
        }
        
        async function newSession() {
            try {
                const response = await fetch('/new_session', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        user_id: userId
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    sessionId = data.session_id;
                    addMessage('✓ New session created', 'bot');
                    updateStatus();
                } else {
                    addMessage(`Error creating session: ${data.error}`, 'bot');
                }
            } catch (error) {
                addMessage(`Network error: ${error.message}`, 'bot');
            }
        }
        
        async function saveSession() {
            try {
                const response = await fetch('/save_memory', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        user_id: userId
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    addMessage('✓ Session saved to memory bank', 'bot');
                } else {
                    addMessage(`Error saving session: ${data.error}`, 'bot');
                }
            } catch (error) {
                addMessage(`Network error: ${error.message}`, 'bot');
            }
        }
        
        function clearChat() {
            const messagesContainer = document.getElementById('messages');
            messagesContainer.innerHTML = '<div class="message bot-message">Chat cleared. How can I help you?</div>';
        }
        
        function updateStatus() {
            const sessionSpan = document.getElementById('sessionId');
            sessionSpan.textContent = sessionId ? sessionId.substring(0, 8) + '...' : 'Not created';
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
        // Initialize
        updateStatus();
    </script>
</body>
</html>
        """
        
    async def cleanup(self):
        """Cleanup resources"""
        if self.agent_engine:
            try:
                self.agent_engine.delete()
                print("✓ Agent engine cleaned up")
            except Exception as e:
                print(f"Error cleaning up agent engine: {e}")

# Simple web server using Python's built-in HTTP server
import http.server
import socketserver
import urllib.parse
import threading

class ADKWebHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, adk_interface=None, **kwargs):
        self.adk_interface = adk_interface
        super().__init__(*args, **kwargs)
        
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.adk_interface.generate_html_interface().encode())
        else:
            self.send_error(404)
            
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            
            if self.path == '/chat':
                result = asyncio.run(self.adk_interface.chat(
                    data['user_id'], 
                    data['message']
                ))
            elif self.path == '/new_session':
                result = asyncio.run(self.adk_interface.new_session(
                    data['user_id']
                ))
            elif self.path == '/save_memory':
                result = asyncio.run(self.adk_interface.save_session_to_memory(
                    data['user_id']
                ))
            else:
                result = {"success": False, "error": "Unknown endpoint"}
                
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {"success": False, "error": str(e)}
            self.wfile.write(json.dumps(error_response).encode())

async def run_web_server():
    """Run the ADK web interface"""
    adk_interface = ADKWebInterface()
    
    try:
        await adk_interface.initialize()
        
        # Create handler with ADK interface
        handler = lambda *args, **kwargs: ADKWebHandler(*args, adk_interface=adk_interface, **kwargs)
        
        PORT = int(os.environ.get("WEB_PORT", 8080))
        
        with socketserver.TCPServer(("", PORT), handler) as httpd:
            print(f"🌐 ADK Web Interface running at http://localhost:{PORT}")
            print("Press Ctrl+C to stop the server")
            
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nShutting down web server...")
                
    except Exception as e:
        print(f"❌ Error running web server: {e}")
        
    finally:
        await adk_interface.cleanup()

if __name__ == "__main__":
    asyncio.run(run_web_server())