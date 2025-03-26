"""
TripMate Agent - A travel search agent with attitude, real-time data, and efficient caching
"""

import os
import json
import time
import hashlib
from datetime import date, datetime, timedelta
import requests
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Get API keys from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SERP_API_KEY = os.getenv("SERP_API_KEY")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Airport codes mapping for common cities
AIRPORT_CODES = {
    "delhi": "DEL",
    "mumbai": "BOM",
    "chennai": "MAA",
    "kolkata": "CCU",
    "bengaluru": "BLR",
    "bangalore": "BLR",
    "hyderabad": "HYD",
    "bali": "DPS",
    "denpasar": "DPS",
    "bangkok": "BKK",
    "new york": "JFK",
    "london": "LHR",
    "paris": "CDG",
    "dubai": "DXB",
    "singapore": "SIN",
    "tokyo": "HND",
    "sydney": "SYD",
    "agra": "AGR"  # Note: Agra's airport is small, often Delhi is used instead
}


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

        # Track if this is the first interaction
        self.is_first_interaction = True

    def get_airport_code(self, city):
        """Get airport code for city name."""
        if not city:
            return None

        city_lower = city.lower()
        return AIRPORT_CODES.get(city_lower, city_lower)

    def _generate_cache_key(self, params):
        """Generate a unique cache key based on search parameters."""
        # Convert params dict to a sorted, stringified version for consistent hashing
        param_str = json.dumps(params, sort_keys=True)
        # Create a hash of the parameters
        return hashlib.md5(param_str.encode()).hexdigest()

    def search_hotels(self, location, check_in_date, check_out_date, adults=1, force_refresh=False):
        """Search for hotels using SERP API with the correct endpoint and caching."""
        try:
            # Create a params dictionary for cache key generation
            search_params = {
                "location": location,
                "check_in_date": check_in_date,
                "check_out_date": check_out_date,
                "adults": adults
            }

            # Generate cache key
            cache_key = self._generate_cache_key(search_params)

            # Check if we have cached results and are not forcing a refresh
            if not force_refresh and cache_key in self.cache["hotel_search"]:
                print(f"\nUsing cached hotel results for {location}")
                return self.cache["hotel_search"][cache_key]["results"]

            # Format the query string properly
            query = f"{location} Hotels"
            query_encoded = requests.utils.quote(query)

            # Build URL according to SERP API docs
            url = f"https://serpapi.com/search.json?engine=google_hotels&q={query_encoded}&check_in_date={check_in_date}&check_out_date={check_out_date}&adults={adults}&currency=USD&gl=us&hl=en&api_key={SERP_API_KEY}"

            print(
                f"\nHotel search URL: {url.replace(SERP_API_KEY, 'API_KEY_HIDDEN')}")

            response = requests.get(url)
            data = response.json()

            print(f"\nHotel API response status: {response.status_code}")
            print(
                f"Hotel API response keys: {list(data.keys()) if data else 'No data'}")

            # Extract the most relevant hotel information
            hotels = []
            if "properties" in data:
                for hotel in data["properties"][:5]:  # Limit to top 5 hotels
                    hotels.append({
                        "name": hotel.get("name", "Unknown"),
                        "price": hotel.get("price", "Unknown"),
                        "rating": hotel.get("rating", "Unknown"),
                        "reviews": hotel.get("reviews", "Unknown"),
                        "location": hotel.get("address", "Unknown"),
                        "thumbnail": hotel.get("thumbnail", None),
                        "link": hotel.get("link", None)
                    })

                print(f"Found {len(hotels)} hotels")

                # Cache the results
                self.cache["hotel_search"][cache_key] = {
                    "parameters": search_params,
                    "timestamp": time.time(),
                    "results": hotels
                }
            else:
                print("No properties found in hotel data")
                if "error" in data:
                    print(f"API Error: {data['error']}")

            return hotels if hotels else []

        except Exception as e:
            print(f"Hotel search error: {str(e)}")
            return []

    def search_flights(self, origin, destination, departure_date, return_date=None, adults=1, force_refresh=False):
        """Search for flights using SERP API with the correct endpoint and caching."""
        try:
            # Get airport codes if available
            origin_code = self.get_airport_code(origin)
            dest_code = self.get_airport_code(destination)

            # Create a params dictionary for cache key generation
            search_params = {
                "origin": origin_code,
                "destination": dest_code,
                "departure_date": departure_date,
                "return_date": return_date,
                "adults": adults
            }

            # Generate cache key
            cache_key = self._generate_cache_key(search_params)

            # Check if we have cached results and are not forcing a refresh
            if not force_refresh and cache_key in self.cache["flight_search"]:
                print(
                    f"\nUsing cached flight results for {origin} to {destination}")
                return self.cache["flight_search"][cache_key]["results"]

            # Base URL for Google Flights search according to SERP API docs
            url = f"https://serpapi.com/search.json?engine=google_flights&departure_id={origin_code}&arrival_id={dest_code}&outbound_date={departure_date}"

            # Add return date if provided
            if return_date:
                url += f"&return_date={return_date}"

            # Add other parameters
            url += f"&currency=USD&hl=en&api_key={SERP_API_KEY}"

            print(
                f"\nFlight search URL: {url.replace(SERP_API_KEY, 'API_KEY_HIDDEN')}")

            response = requests.get(url)
            data = response.json()

            print(f"\nFlight API response status: {response.status_code}")
            print(
                f"Flight API response keys: {list(data.keys()) if data else 'No data'}")

            # Extract flight information - FIXED: look for best_flights and other_flights
            flights = []

            # Check best_flights first
            if "best_flights" in data and data["best_flights"]:
                print("Found flights in 'best_flights'")
                for flight in data["best_flights"][:3]:  # Get top 3 best flights
                    flight_info = {
                        "type": "Best Flight",
                        "airline": flight.get("airline", "Unknown"),
                        "price": flight.get("price", "Unknown"),
                        "duration": flight.get("duration", "Unknown"),
                        "departure_time": flight.get("departure_time", "Unknown"),
                        "arrival_time": flight.get("arrival_time", "Unknown"),
                        "stops": flight.get("stops", "Unknown")
                    }
                    flights.append(flight_info)

            # Then check other_flights
            if "other_flights" in data and data["other_flights"]:
                print("Found flights in 'other_flights'")
                for flight in data["other_flights"][:2]:  # Get top 2 other flights
                    flight_info = {
                        "type": "Alternative Flight",
                        "airline": flight.get("airline", "Unknown"),
                        "price": flight.get("price", "Unknown"),
                        "duration": flight.get("duration", "Unknown"),
                        "departure_time": flight.get("departure_time", "Unknown"),
                        "arrival_time": flight.get("arrival_time", "Unknown"),
                        "stops": flight.get("stops", "Unknown")
                    }
                    flights.append(flight_info)

            print(f"Found total of {len(flights)} flights")

            # Cache the results if we found any
            if flights:
                self.cache["flight_search"][cache_key] = {
                    "parameters": search_params,
                    "timestamp": time.time(),
                    "results": flights
                }
            else:
                print("No flights found in data")
                if "error" in data:
                    print(f"API Error: {data['error']}")

            return flights

        except Exception as e:
            print(f"Flight search error: {str(e)}")
            return []

    def _update_memory(self, new_info):
        """Update agent memory with new information, preserving existing data."""
        for key, value in new_info.items():
            # Only update if the new value is not None and either:
            # 1. The current value is None, or
            # 2. The new value is different from current (for overriding)
            if value is not None and (self.memory.get(key) is None or value != self.memory.get(key)):
                self.memory[key] = value

        # Special handling for transit_cities as it's a list
        if new_info.get("transit_cities") and isinstance(new_info["transit_cities"], list):
            for city in new_info["transit_cities"]:
                if city and city not in self.memory["transit_cities"]:
                    self.memory["transit_cities"].append(city)

        # Special handling for transportation as it's a list
        if new_info.get("transportation") and isinstance(new_info["transportation"], list):
            for mode in new_info["transportation"]:
                if mode and mode not in self.memory["transportation"]:
                    self.memory["transportation"].append(mode)

    def _extract_travel_info(self, user_prompt):
        """Extract travel information from user prompt and update memory."""
        extraction_prompt = f"""
        Extract travel information from this user query. Format the response as a JSON object with these fields:
        - origin: The origin city/location
        - destination: The destination city/location for the trip
        - transit_cities: Any cities mentioned for transit (e.g., "I will fly from Delhi" when origin is different)
        - check_in_date: In YYYY-MM-DD format if specified
        - check_out_date: In YYYY-MM-DD format if specified
        - budget: Any budget mentioned (just the number, not the currency)
        - hotel_preference: Any hotel preferences (e.g., "hostel", "5-star", etc.)
        - num_adults: Number of travelers, default to 1 if not specified
        - transportation: Types of transportation mentioned (e.g., "flight", "train", etc.)
        
        IMPORTANT: For dates, convert natural language to YYYY-MM-DD format.
        For example, "5th April" should be converted to "2025-04-05" 
        (assuming current year is 2025 if not specified).
        
        If the user is asking to change dates (like "I want to go tomorrow" or "what about next month"),
        calculate the new date based on the current date which is {self.today}.
        
        Previous information I already know (only extract new or different information):
        {json.dumps(self.memory, indent=2)}
        
        User query: {user_prompt}
        
        JSON response:
        """

        response = self.model.generate_content(extraction_prompt)

        try:
            # Try to parse the JSON response
            json_str = response.text.strip().strip('```json').strip('```').strip()
            new_info = json.loads(json_str)
            print(f"Extracted info: {new_info}")

            # Update memory with new information
            self._update_memory(new_info)

        except Exception as e:
            print(f"Error parsing travel info: {str(e)}")
            # Just continue with existing memory

        return self.memory

    def _make_reasonable_assumptions(self):
        """Fill in missing details with reasonable assumptions."""
        today = datetime.now()

        # If we have destination but no check-in date, assume two weeks from now
        if self.memory["destination"] and not self.memory["check_in_date"]:
            future_date = today + timedelta(days=14)
            self.memory["check_in_date"] = future_date.strftime('%Y-%m-%d')

        # If we have check-in but no check-out, assume a 7-day stay
        if self.memory["check_in_date"] and not self.memory["check_out_date"]:
            check_in = datetime.strptime(
                self.memory["check_in_date"], '%Y-%m-%d')
            check_out = check_in + timedelta(days=7)
            self.memory["check_out_date"] = check_out.strftime('%Y-%m-%d')

        # If we have a destination but no hotel preference, assume 3-star
        if self.memory["destination"] and not self.memory["hotel_preference"]:
            self.memory["hotel_preference"] = "3-star"

        # If we have origin and destination but no transportation, assume flight
        if self.memory["origin"] and self.memory["destination"] and not self.memory["transportation"]:
            self.memory["transportation"] = ["flight"]

        return self.memory

    def _should_refresh_searches(self, user_prompt):
        """Determine if we need to refresh search results based on user prompt."""
        # Keywords that might indicate the user wants fresh results
        refresh_keywords = [
            "search again", "check again", "refresh", "update", "new search",
            "latest", "current", "fresh", "now", "today", "find me", "get me"
        ]

        # Check if any refresh keywords are in the user prompt
        for keyword in refresh_keywords:
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

            # Extract travel information and update memory
            trip_info = self._extract_travel_info(user_prompt)

            # Make reasonable assumptions for missing data
            self._make_reasonable_assumptions()

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

                # Search for hotels if we have destination and dates
                # Only search if we have no results OR parameters have changed OR force refresh
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
                        hotels = self.search_hotels(
                            self.memory["destination"],
                            self.memory["check_in_date"],
                            self.memory["check_out_date"],
                            self.memory.get("num_adults", 1),
                            force_refresh
                        )
                    else:
                        print(
                            f"\nReusing existing hotel results for {self.memory['destination']}")
                        # Get cached results based on current parameters
                        search_params = {
                            "location": self.memory["destination"],
                            "check_in_date": self.memory["check_in_date"],
                            "check_out_date": self.memory["check_out_date"],
                            "adults": self.memory.get("num_adults", 1)
                        }
                        cache_key = self._generate_cache_key(search_params)

                        if cache_key in self.cache["hotel_search"]:
                            hotels = self.cache["hotel_search"][cache_key]["results"]
                        else:
                            # If not in cache for some reason, do a fresh search
                            hotels = self.search_hotels(
                                self.memory["destination"],
                                self.memory["check_in_date"],
                                self.memory["check_out_date"],
                                self.memory.get("num_adults", 1),
                                True
                            )

                    search_results["hotels"] = hotels

                    # Add a small delay between API calls if we're doing both
                    time.sleep(1)

                # Search for flights if needed
                # Only search if we have no results OR parameters have changed OR force refresh
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
                            flights = self.search_flights(
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
                            # Get cached results based on current parameters
                            search_params = {
                                "origin": self.get_airport_code(flight_origin),
                                "destination": self.get_airport_code(self.memory["destination"]),
                                "departure_date": self.memory["check_in_date"],
                                "return_date": self.memory.get("check_out_date"),
                                "adults": self.memory.get("num_adults", 1)
                            }
                            cache_key = self._generate_cache_key(search_params)

                            if cache_key in self.cache["flight_search"]:
                                flights = self.cache["flight_search"][cache_key]["results"]
                            else:
                                # If not in cache for some reason, do a fresh search
                                flights = self.search_flights(
                                    flight_origin,
                                    self.memory["destination"],
                                    self.memory["check_in_date"],
                                    self.memory.get("check_out_date"),
                                    self.memory.get("num_adults", 1),
                                    True
                                )

                        search_results["flights"] = flights

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

            # Now, generate a response using the search results
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

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Detailed error: {error_details}")
            return f"Ugh, something went wrong. Even AI has bad days! Error: {str(e)}"
