#!/usr/bin/env python3
"""
Simple script to check memory bank entries
"""

import asyncio
import os
from google.adk.memory import VertexAiMemoryBankService
from dotenv import load_dotenv

load_dotenv()

async def main():
    memory_service = VertexAiMemoryBankService(
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        agent_engine_id=os.getenv("AGENT_ENGINE_ID")
    )
    
    try:
        # Search for any memories
        results = await memory_service.search_memory(
            user_id="user",
            query="",
            limit=10
        )
        
        print(f"Found {len(results.memories)} memories:")
        for i, memory in enumerate(results.memories, 1):
            print(f"{i}. {memory}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())