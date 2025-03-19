#!/usr/bin/env python
"""
TripMate - AI-powered Travel Automation Agent

Main script to run TripMate for travel planning tasks.
"""

import os
from dotenv import load_dotenv
from tripmate.agent import TripMateAgent

# Load environment variables
load_dotenv()

# Check for required environment variables
required_env_vars = ["GOOGLE_CLOUD_PROJECT_ID", "SERP_API_KEY"]
for var in required_env_vars:
    if not os.getenv(var):
        raise ValueError(f"{var} is not set. Please add it to your .env file.")


def main():
    """
    Main function to run TripMate agent interactively.
    """
    print("Welcome to TripMate - Your Sassy Travel Assistant!")
    print("I'll help you plan your next adventure.")
    print("What trip can I help you plan today? (Type 'exit' to quit)")

    # Initialize TripMate agent
    agent = TripMateAgent()

    while True:
        # Get user input
        user_input = input("\nYou: ")

        # Check if user wants to exit
        if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
            print(
                "\nTripMate: Fine, bye then! Come back when you actually want to go somewhere cool.")
            break

        # Process user request
        print("\nTripMate is planning... (this might take a moment)")
        try:
            response = agent.plan_trip(user_input)
            print("\nTripMate:", response)
        except Exception as e:
            print(
                f"\nTripMate: Ugh, something went wrong. Even AI has bad days! Error: {str(e)}")


if __name__ == "__main__":
    main()
