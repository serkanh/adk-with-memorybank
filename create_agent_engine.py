#!/usr/bin/env python3
"""
Create Agent Engine for ADK Memory Bot
Based on express-mode.ipynb example
"""

import os
import json
import asyncio
from google import genai

# Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

async def create_agent_engine():
    """Create Agent Engine using GenAI SDK"""
    print("🚀 Creating Agent Engine...")
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    
    try:
        # Create Agent Engine with GenAI SDK
        client = genai.Client(vertexai=True)._api_client
        string_response = client.request(
            http_method='POST',
            path=f'reasoningEngines',
            request_dict={
                "displayName": "ADK-Memory-Bot-Engine", 
                "description": "Agent Engine for ADK Memory Bot with Vertex AI Memory Bank integration"
            },
        ).body
        
        response = json.loads(string_response)
        
        # Extract APP_NAME and APP_ID
        app_name = "/".join(response['name'].split("/")[:6])
        app_id = app_name.split('/')[-1]
        
        print("✅ Agent Engine created successfully!")
        print(f"   Full Name: {response['name']}")
        print(f"   APP_NAME: {app_name}")
        print(f"   APP_ID: {app_id}")
        print(f"   Display Name: {response.get('displayName', 'N/A')}")
        print(f"   Description: {response.get('description', 'N/A')}")
        
        # Save to environment file
        env_content = f"""# Google Cloud / Vertex AI Configuration
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT={PROJECT_ID}
GOOGLE_CLOUD_LOCATION={LOCATION}

# Agent Engine Configuration
AGENT_ENGINE_ID={app_id}
AGENT_ENGINE_NAME={app_name}

# Application Configuration
APP_NAME=adk-memory-bot
DEFAULT_USER_ID=user_123
"""
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("✅ Environment file updated with Agent Engine details")
        
        return {
            "app_name": app_name,
            "app_id": app_id,
            "full_response": response
        }
        
    except Exception as e:
        print(f"❌ Error creating Agent Engine: {e}")
        raise

async def list_existing_engines():
    """List existing Agent Engines"""
    print("\n🔍 Listing existing Agent Engines...")
    
    try:
        client = genai.Client(vertexai=True)._api_client
        string_response = client.request(
            http_method='GET',
            path=f'reasoningEngines',
        ).body
        
        response = json.loads(string_response)
        
        if 'reasoningEngines' in response:
            engines = response['reasoningEngines']
            print(f"Found {len(engines)} existing Agent Engine(s):")
            
            for i, engine in enumerate(engines, 1):
                app_name = "/".join(engine['name'].split("/")[:6])
                app_id = app_name.split('/')[-1]
                
                print(f"\n{i}. {engine.get('displayName', 'Unnamed')}")
                print(f"   APP_ID: {app_id}")
                print(f"   Full Name: {engine['name']}")
                print(f"   Description: {engine.get('description', 'N/A')}")
                
            return engines
        else:
            print("No existing Agent Engines found.")
            return []
            
    except Exception as e:
        print(f"❌ Error listing Agent Engines: {e}")
        return []

async def main():
    """Main function"""
    print("🤖 ADK Agent Engine Setup")
    print("=" * 50)
    
    # List existing engines first
    existing_engines = await list_existing_engines()
    
    if existing_engines:
        print("\n❓ Do you want to:")
        print("1. Create a new Agent Engine")
        print("2. Use an existing Agent Engine")
        
        choice = input("\nEnter your choice (1 or 2): ").strip()
        
        if choice == "2":
            print("\n📝 Update your .env file with the APP_ID from the existing engine above.")
            return
    
    # Create new Agent Engine
    print("\n🔧 Creating new Agent Engine...")
    result = await create_agent_engine()
    
    print("\n" + "=" * 50)
    print("✅ Setup complete!")
    print(f"   Use APP_ID: {result['app_id']}")
    print("   Environment file (.env) has been updated")
    print("\nNext steps:")
    print("1. Update your docker-compose.yml with the new APP_ID")
    print("2. Run: docker-compose up memory-bot-web")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())