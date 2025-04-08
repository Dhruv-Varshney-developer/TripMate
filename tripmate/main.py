#!/usr/bin/env python
"""
TripMate - AI-powered Travel Assistant with Attitude
Main script to run the TripMate agent.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
from tripmate.agent import TripMateAgent
from .ws_server import start_ws_server

# Load environment variables
load_dotenv()

# Check for required environment variables
required_env_vars = ["GEMINI_API_KEY", "SERP_API_KEY"]
missing_vars = []

for var in required_env_vars:
    if not os.getenv(var):
        missing_vars.append(var)

if missing_vars:
    print("Error: The following environment variables are missing:")
    for var in missing_vars:
        print(f"  - {var}")
    print("\nPlease set these variables in your .env file.")
    print("Example .env file:")
    print("GEMINI_API_KEY=your-gemini-api-key")
    print("SERP_API_KEY=your-serp-api-key")
    sys.exit(1)

async def run_cli(agent):
    print("🧳 Welcome to TripMate - Your Sassy Travel Assistant! 🧳")
    while True:
        # Get user input
        user_input = input("\n😎 You: ")

        # Check if user wants to exit
        if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
            print(
                "\n🙄 TripMate: Fine, bye then! Come back when you actually want to go somewhere cool.")
            break

        # Check if user wants to reset the conversation
        if user_input.lower() in ["reset", "start over", "new trip", "clear"]:
            print(
                "\n🔄 TripMate: Alright, wiping the slate clean! Let's start fresh. Where to next?")
            # Reinitialize the agent to clear memory
            agent = TripMateAgent()
            continue

        # Process user request
        print("\n⏳ TripMate is planning... (this might take a moment)")
        try:
            response = agent.plan_trip(user_input)
            print("\n😏 TripMate:", response)
        except Exception as e:
            print(
                f"\n😤 TripMate: Ugh, something went wrong. Even AI has bad days! Error: {str(e)}")


async def main():
    """
    Main function to run TripMate agent interactively.
    """
    print("🧳 Welcome to TripMate - Your Sassy Travel Assistant! 🧳")
    print("I'll help you plan your next adventure (with attitude).")
    print("What trip can I help you plan today? (Type 'exit' to quit)")

    agent = TripMateAgent()
    await start_ws_server()
    await run_cli(agent)

if __name__ == "__main__":
    asyncio.run(main())
    
