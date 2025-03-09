#!/usr/bin/env python
"""
TripMate - AI-powered Travel Automation Agent

Main script to run TripMate for travel automation tasks.
"""

import os
import asyncio
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from tripmate.agent import TripMateAgent

# Load environment variables
load_dotenv()

# Ensure required environment variables are set
required_env_vars = ["OPENAI_API_KEY"]
for var in required_env_vars:
    if not os.getenv(var):
        raise ValueError(f"{var} is not set. Please add it to your .env file.")

async def main():
    """
    Main function to run TripMate agent
    """
    # Get user travel prompt
    travel_prompt = input("Please enter your travel requirements: ")
    
    if not travel_prompt:
        travel_prompt = "Find and book a round-trip flight from New York to London for next month with a budget of $800."
        print(f"Using default prompt: {travel_prompt}")
    
    # Initialize language model
    llm = ChatOpenAI(model="gpt-4o")
    
    # Initialize TripMate agent
    agent = TripMateAgent(
        travel_prompt=travel_prompt,
        llm=llm,
        headless=False  # Set to True in production
    )
    
    # Run the agent
    print("\nRunning TripMate agent...\n")
    result = await agent.run()
    
    # Print the result
    print("\nResult:")
    print(result)

if __name__ == "__main__":
    asyncio.run(main()) 