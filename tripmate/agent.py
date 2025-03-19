"""
TripMate Agent Module - Implementation using Google Gemini 1.5 Pro
"""

import os
from datetime import date
import requests
from dotenv import load_dotenv
import vertexai
from vertexai.preview.generative_models import (
    GenerativeModel, FunctionDeclaration, Tool, Content, Part
)

# Load environment variables
load_dotenv()

# Get API keys from environment variables
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
SERP_API_KEY = os.getenv("SERP_API_KEY")


class TripMateAgent:
    """
    TripMate Agent class for travel planning using Google Gemini 1.5 Pro.
    """

    def __init__(self):
        """Initialize the TripMate agent."""
        # Initialize Vertex AI
        vertexai.init(project=PROJECT_ID, location=LOCATION)

        # Define API functions
        self._define_api_functions()

        # Define function declarations
        self._define_function_declarations()

        # Create function tools
        self.tools = Tool(function_declarations=[
            self.hotel_function,
            self.flight_function,
            self.attraction_function
        ])

        # Configure safety settings
        self._configure_safety_settings()

        # Initialize the model
        self.model = GenerativeModel(
            model_name='gemini-1.5-pro-001',
            generation_config=self.generation_config,
            safety_settings=self.safety_settings,
            tools=[self.tools]
        )

        # Create a mapping of function names to their implementations
        self.callable_functions = {
            "hotel_api": self.hotel_api,
            "flight_api": self.flight_api,
            "attraction_api": self.attraction_api
        }

        # Get today's date
        self.today = date.today()

    def _define_api_functions(self):
        """Define the API functions for travel information."""

        def hotel_api(query: str, check_in_date: str, check_out_date: str, hotel_class: int = 3, adults: int = 2):
            """Retrieves hotel information based on location, dates, and preferences."""
            URL = f"https://serpapi.com/search.json?api_key={SERP_API_KEY}&engine=google_hotels&q={query}&check_in_date={check_in_date}&check_out_date={check_out_date}&adults={int(adults)}&hotel_class={int(hotel_class)}&currency=USD&gl=us&hl=en"
            response = requests.get(URL).json()
            return response.get("properties", [])

        def flight_api(origin: str, destination: str, departure_date: str, return_date: str = None, adults: int = 1):
            """Retrieves flight information based on origin, destination, and dates."""
            base_url = f"https://serpapi.com/search.json?api_key={SERP_API_KEY}&engine=google_flights"
            query_params = f"&departure_id={origin}&arrival_id={destination}&outbound_date={departure_date}"

            if return_date:
                query_params += f"&return_date={return_date}"

            query_params += f"&adults={adults}&currency=USD"
            URL = base_url + query_params

            response = requests.get(URL).json()
            return response.get("flights", [])

        def attraction_api(query: str):
            """Retrieves tourist attraction information based on a location query."""
            URL = f"https://serpapi.com/search.json?api_key={SERP_API_KEY}&engine=google&q=top attractions in {query}&hl=en&gl=us"
            response = requests.get(URL).json()
            return response.get("organic_results", [])

        # Set the functions as instance methods
        self.hotel_api = hotel_api
        self.flight_api = flight_api
        self.attraction_api = attraction_api

    def _define_function_declarations(self):
        """Define function declarations for the Gemini model."""

        self.hotel_function = FunctionDeclaration(
            name="hotel_api",
            description="Retrieves hotel information based on location, dates, and optional preferences.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Parameter defines the search query for hotels (e.g., 'Hotels in New York')."
                    },
                    "check_in_date": {
                        "type": "string",
                        "description": "Check-in date in YYYY-MM-DD format (e.g., '2024-04-30')."
                    },
                    "check_out_date": {
                        "type": "string",
                        "description": "Check-out date in YYYY-MM-DD format (e.g., '2024-05-01')."
                    },
                    "hotel_class": {
                        "type": "integer",
                        "description": """Hotel class (star rating).
                        
                        Options:
                        - 2: 2-star
                        - 3: 3-star
                        - 4: 4-star
                        - 5: 5-star
                        """
                    },
                    "adults": {
                        "type": "integer",
                        "description": "Number of adults (e.g., 1 or 2)."
                    }
                },
                "required": ["query", "check_in_date", "check_out_date"]
            }
        )

        self.flight_function = FunctionDeclaration(
            name="flight_api",
            description="Retrieves flight information based on origin, destination, and dates.",
            parameters={
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": "Origin airport or city code (e.g., 'NYC' or 'New York')."
                    },
                    "destination": {
                        "type": "string",
                        "description": "Destination airport or city code (e.g., 'LAX' or 'Los Angeles')."
                    },
                    "departure_date": {
                        "type": "string",
                        "description": "Departure date in YYYY-MM-DD format (e.g., '2024-04-30')."
                    },
                    "return_date": {
                        "type": "string",
                        "description": "Optional return date in YYYY-MM-DD format for round-trip flights (e.g., '2024-05-15')."
                    },
                    "adults": {
                        "type": "integer",
                        "description": "Number of adult passengers (e.g., 1 or 2)."
                    }
                },
                "required": ["origin", "destination", "departure_date"]
            }
        )

        self.attraction_function = FunctionDeclaration(
            name="attraction_api",
            description="Retrieves tourist attraction information based on a location query.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The location to search for attractions (e.g., 'Paris, France')."
                    }
                },
                "required": ["query"]
            }
        )

    def _configure_safety_settings(self):
        """Configure generation and safety settings."""

        self.generation_config = {
            "max_output_tokens": 2048,  # Increased for more detailed responses
            "temperature": 0.7,
            "top_p": 0.8,
        }

    def _mission_prompt(self, prompt: str):
        """Create a mission prompt with sassy personality for TripMate."""

        return f"""
        You are TripMate, a sassy but helpful travel assistant with attitude. Your job is to help users plan trips by finding relevant information about destinations, flights, hotels, and attractions.
        
        Think through what the user is asking for and determine which tools you need to use to help them. Be efficient and accurate, but keep your sassy personality.
        
        Today's date is {self.today}.
        
        User's request: {prompt}
        
        First, identify what the user is looking for and what information you need to gather. Then use the appropriate tools to find the information.
        
        For flights, you need origin, destination and dates.
        For hotels, you need location, check-in date, and check-out date.
        For attractions, you just need the location.
        
        If the user doesn't provide all necessary information, ask them for it in a sassy but helpful way.
        
        Once you have gathered all information, provide the user with 4-5 best options based on their preferences.
        Keep your answers concise and to the point, but make sure they're helpful.
        """.strip()

    def plan_trip(self, user_prompt):
        """
        Plan a trip based on the user's prompt.

        Args:
            user_prompt (str): The user's travel planning prompt.

        Returns:
            str: The agent's response with travel recommendations.
        """
        # Start a chat session
        chat = self.model.start_chat()

        # Format the prompt with mission details
        prompt = self._mission_prompt(user_prompt)

        # Send the message and get response
        response = chat.send_message(prompt)

        # Handle function calls
        tools = response.candidates[0].function_calls if hasattr(
            response.candidates[0], 'function_calls') else []

        # Process function calls iteratively
        while tools:
            for tool in tools:
                # Call the appropriate function
                try:
                    function_res = self.callable_functions[tool.name](
                        **tool.args)
                    # Send function response back to the model
                    response = chat.send_message(
                        Content(
                            role="function_response",
                            parts=[
                                Part.from_function_response(
                                    name=tool.name,
                                    response={"result": function_res}
                                )
                            ]
                        )
                    )
                except Exception as e:
                    # Handle errors gracefully
                    error_message = f"Error calling {tool.name}: {str(e)}"
                    response = chat.send_message(
                        Content(
                            role="function_response",
                            parts=[
                                Part.from_function_response(
                                    name=tool.name,
                                    response={"error": error_message}
                                )
                            ]
                        )
                    )

            # Check if there are more function calls
            tools = response.candidates[0].function_calls if hasattr(
                response.candidates[0], 'function_calls') else []

        return response.text
