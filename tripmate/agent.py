"""
TripMate Agent - A travel search agent with attitude, real-time data, and efficient caching
"""

import os
import json
import time
from datetime import date
from dotenv import load_dotenv
import google.generativeai as genai

from .hotel_service import HotelService
from .flight_service import FlightService
from .extractor import TravelInfoExtractor
from .utils import make_reasonable_assumptions
from .constants import REFRESH_KEYWORDS

# Load environment variables
load_dotenv()

# Get API keys from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SERP_API_KEY = os.getenv("SERP_API_KEY")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)


class TripMateAgent:
    """
    TripMate Agent class for travel planning with memory between interactions.
    """

    def __init__(self):
        """Initialize the TripMate agent with conversation memory."""
        # Get today's date
        self.today = date.today()

        # Initialize the Gemini model
        self.model = genai.GenerativeModel('gemini-1.5-pro')

        # Create a chat session to maintain history
        self.chat = self.model.start_chat(history=[])

        # Initialize memory to store travel details across interactions
        self.memory = {
            "origin": None,
            "destination": None,
            "transit_cities": [],
            "check_in_date": None,
            "check_out_date": None,
            "budget": None,
            "hotel_preference": None,
            "num_adults": 1,
            "transportation": []
        }

        # Initialize cache for API results to avoid redundant calls
        self.cache = {
            "hotel_search": {},
            "flight_search": {}
        }

        # Initialize services
        self.hotel_service = HotelService(
            SERP_API_KEY, self.cache["hotel_search"])
        self.flight_service = FlightService(
            SERP_API_KEY, self.cache["flight_search"])
        self.extractor = TravelInfoExtractor(self.model)

        # Track if this is the first interaction
        self.is_first_interaction = True

    def _should_refresh_searches(self, user_prompt):
        """Determine if we need to refresh search results based on user prompt."""
        # Check if any refresh keywords are in the user prompt
        for keyword in REFRESH_KEYWORDS:
            if keyword.lower() in user_prompt.lower():
                return True

        return False

    def _have_dates_changed(self, old_info, new_info):
        """Check if travel dates have changed."""
        return (old_info.get("check_in_date") != new_info.get("check_in_date") or
                old_info.get("check_out_date") != new_info.get("check_out_date"))

    def _have_locations_changed(self, old_info, new_info):
        """Check if travel locations have changed."""
        return (old_info.get("origin") != new_info.get("origin") or
                old_info.get("destination") != new_info.get("destination"))

    def plan_trip(self, user_prompt):
        """
        Plan a trip based on the user's prompt, maintaining conversation history.
        """
        try:
            # Store previous state for comparison
            previous_memory = self.memory.copy()

            # Extract travel information
            new_info = self.extractor.extract_travel_info(
                user_prompt, self.memory)

            # Update memory with new information
            self.memory = self.extractor.update_memory(self.memory, new_info)

            # Make reasonable assumptions for missing data
            self.memory = make_reasonable_assumptions(self.memory)

            # Determine if we need to refresh searches
            force_refresh = self._should_refresh_searches(user_prompt)
            dates_changed = self._have_dates_changed(
                previous_memory, self.memory)
            locations_changed = self._have_locations_changed(
                previous_memory, self.memory)

            # Check if we have enough information to start searching
            can_search = (self.memory["destination"] is not None)

            search_results = {
                "prompt": user_prompt,
                "trip_info": self.memory
            }

            # Only perform searches if we have the minimum required info
            if can_search:
                print("\n=== STARTING API SEARCHES ===")
                self._perform_searches(
                    search_results, force_refresh, dates_changed, locations_changed)
                print("\n=== API SEARCHES COMPLETE ===")

            # Determine if this is the first interaction
            is_first = self.is_first_interaction
            self.is_first_interaction = False

            # Print overall search results for debugging
            print("\nFinal search results summary:")
            for key, value in search_results.items():
                if key != "prompt" and key != "trip_info":
                    print(
                        f"- {key}: {len(value) if isinstance(value, list) else 'Not a list'}")

            # Generate response using search results
            return self._generate_response(user_prompt, search_results, is_first)

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Detailed error: {error_details}")
            return f"Ugh, something went wrong. Even AI has bad days! Error: {str(e)}"

    def _perform_searches(self, search_results, force_refresh, dates_changed, locations_changed):
        """Perform hotel and flight searches based on memory."""
        # Search for hotels if we have destination and dates
        if self.memory["destination"] and self.memory["check_in_date"] and self.memory["check_out_date"]:
            should_search_hotels = (
                force_refresh or
                dates_changed or
                locations_changed or
                self.is_first_interaction
            )

            if should_search_hotels:
                print(
                    f"\nSearching for hotels in {self.memory['destination']} from {self.memory['check_in_date']} to {self.memory['check_out_date']}")
                hotels = self.hotel_service.search_hotels(
                    self.memory["destination"],
                    self.memory["check_in_date"],
                    self.memory["check_out_date"],
                    self.memory.get("num_adults", 1),
                    force_refresh
                )
            else:
                print(
                    f"\nReusing existing hotel results for {self.memory['destination']}")
                hotels = self._get_cached_hotels()

            search_results["hotels"] = hotels

            # Add a small delay between API calls if we're doing both
            time.sleep(1)

        # Search for flights if needed
        self._search_flights(search_results, force_refresh,
                             dates_changed, locations_changed)

    def _search_flights(self, search_results, force_refresh, dates_changed, locations_changed):
        """Search for flights based on memory."""
        if ("flight" in self.memory["transportation"] or not self.memory["transportation"]) and self.memory["check_in_date"]:
            flight_origin = None
            if self.memory["transit_cities"] and len(self.memory["transit_cities"]) > 0:
                flight_origin = self.memory["transit_cities"][0]
            elif self.memory["origin"]:
                flight_origin = self.memory["origin"]

            if flight_origin and self.memory["destination"]:
                should_search_flights = (
                    force_refresh or
                    dates_changed or
                    locations_changed or
                    self.is_first_interaction
                )

                if should_search_flights:
                    print(
                        f"\nSearching for flights from {flight_origin} to {self.memory['destination']} on {self.memory['check_in_date']}")
                    flights = self.flight_service.search_flights(
                        flight_origin,
                        self.memory["destination"],
                        self.memory["check_in_date"],
                        self.memory.get("check_out_date"),
                        self.memory.get("num_adults", 1),
                        force_refresh
                    )
                else:
                    print(
                        f"\nReusing existing flight results for {flight_origin} to {self.memory['destination']}")
                    flights = self._get_cached_flights(flight_origin)

                search_results["flights"] = flights

    def _get_cached_hotels(self):
        """Get cached hotel results based on current parameters."""
        search_params = {
            "location": self.memory["destination"],
            "check_in_date": self.memory["check_in_date"],
            "check_out_date": self.memory["check_out_date"],
            "adults": self.memory.get("num_adults", 1)
        }

        # Try to find matching cache entry
        for cache_key, cache_data in self.hotel_service.cache.items():
            if self._params_match(cache_data["parameters"], search_params):
                return cache_data["results"]

        # If no cache match found, do a fresh search
        return self.hotel_service.search_hotels(
            self.memory["destination"],
            self.memory["check_in_date"],
            self.memory["check_out_date"],
            self.memory.get("num_adults", 1),
            True
        )

    def _get_cached_flights(self, origin):
        """Get cached flight results based on current parameters."""
        search_params = {
            "origin": origin,
            "destination": self.memory["destination"],
            "departure_date": self.memory["check_in_date"],
            "return_date": self.memory.get("check_out_date"),
            "adults": self.memory.get("num_adults", 1)
        }

        # Try to find matching cache entry
        for cache_key, cache_data in self.flight_service.cache.items():
            if self._params_match(cache_data["parameters"], search_params):
                return cache_data["results"]

        # If no cache match found, do a fresh search
        return self.flight_service.search_flights(
            origin,
            self.memory["destination"],
            self.memory["check_in_date"],
            self.memory.get("check_out_date"),
            self.memory.get("num_adults", 1),
            True
        )

    def _params_match(self, params1, params2):
        """Check if two parameter sets match for cache lookup."""
        for key in params1:
            if key in params2 and params1[key] != params2[key]:
                return False
        return True

    def _generate_response(self, user_prompt, search_results, is_first):
        """Generate a response using search results."""
        response_prompt = f"""
        You are TripMate, a sassy and helpful travel assistant with attitude who specializes in travel search. 
        Your job is to provide concrete travel options based on the information available.
        
        The user asked: "{user_prompt}"
        
        Based on all our conversations, here's what I know and have found:
        {json.dumps(search_results, indent=2)}
        
        Respond with specific information, following these guidelines:
        - Focus on providing CONCRETE search results first, then sassy commentary second
        - If you have actual flight, hotel, or train results from the API, SHOW THEM IN DETAIL with specific prices, times and information
        - Don't just tease information - if you have it, provide it fully
        - If you received empty results from searches, clearly state that no results were found
        - For attractions, provide 3-5 concrete suggestions for the destination from your knowledge
        - Make reasonable assumptions about missing information rather than asking too many questions
        - Be concise with your sass and focus more on delivering the actual search results
        - If this is the user's first question ({is_first}), be more welcoming and helpful
        - Format the results in clear sections using markdown (bold headers, bullet points)
        
        Today's date for reference is {self.today}.
        """

        # Send to chat to maintain history
        response = self.chat.send_message(response_prompt)
        return response.text
