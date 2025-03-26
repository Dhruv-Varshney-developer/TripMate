"""
TripMate Agent - A travel planner with attitude
"""

import os
import json
from datetime import date
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


class TripMateAgent:
    """
    TripMate Agent class for travel planning.
    """

    def __init__(self):
        """Initialize the TripMate agent."""
        # Get today's date
        self.today = date.today()

    def search_hotels(self, location, check_in_date, check_out_date, hotel_class=3, adults=1):
        """Search for hotels using SERP API."""
        try:
            url = f"https://serpapi.com/search.json?engine=google_hotels&q=hotels+in+{location}&check_in_date={check_in_date}&check_out_date={check_out_date}&adults={adults}&hotel_class={hotel_class}&currency=USD&api_key={SERP_API_KEY}"
            response = requests.get(url)
            data = response.json()

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
                    })

            return hotels if hotels else []

        except Exception as e:
            print(f"Hotel search error: {str(e)}")
            return []

    def search_flights(self, origin, destination, departure_date, return_date=None, adults=1):
        """Search for flights using SERP API."""
        try:
            # Base URL for Google Flights search
            url = f"https://serpapi.com/search.json?engine=google_flights&departure_id={origin}&arrival_id={destination}&outbound_date={departure_date}"

            # Add return date if provided
            if return_date:
                url += f"&return_date={return_date}"

            # Add other parameters
            url += f"&adults={adults}&currency=USD&api_key={SERP_API_KEY}"

            response = requests.get(url)
            data = response.json()

            # Extract flight information
            flights = []
            if "flights" in data:
                for flight in data["flights"][:5]:  # Limit to top 5 flights
                    flights.append({
                        "airline": flight.get("airline", "Unknown"),
                        "price": flight.get("price", "Unknown"),
                        "duration": flight.get("duration", "Unknown"),
                        "departure_time": flight.get("departure_time", "Unknown"),
                        "arrival_time": flight.get("arrival_time", "Unknown"),
                        "stops": flight.get("stops", "Unknown")
                    })

            return flights if flights else []

        except Exception as e:
            print(f"Flight search error: {str(e)}")
            return []

    def search_attractions(self, location):
        """Search for tourist attractions using SERP API."""
        try:
            url = f"https://serpapi.com/search.json?engine=google&q=top+attractions+in+{location}&hl=en&gl=us&api_key={SERP_API_KEY}"
            response = requests.get(url)
            data = response.json()

            # Extract attraction information
            attractions = []
            if "organic_results" in data:
                for result in data["organic_results"][:8]:  # Limit to top 8 attractions
                    attractions.append({
                        "title": result.get("title", "Unknown"),
                        "snippet": result.get("snippet", "No description available")
                    })

            return attractions if attractions else []

        except Exception as e:
            print(f"Attraction search error: {str(e)}")
            return []

    def search_trains(self, origin, destination, date):
        """Search for trains using SERP API."""
        try:
            url = f"https://serpapi.com/search.json?engine=google&q=trains+from+{origin}+to+{destination}+on+{date}&hl=en&gl=us&api_key={SERP_API_KEY}"
            response = requests.get(url)
            data = response.json()

            # Extract information that might be related to trains
            trains = []
            if "organic_results" in data:
                for result in data["organic_results"][:5]:
                    if any(keyword in result.get("title", "").lower() for keyword in ["train", "rail", "irctc"]):
                        trains.append({
                            "title": result.get("title", "Unknown"),
                            "snippet": result.get("snippet", "No details available")
                        })

            return trains if trains else []

        except Exception as e:
            print(f"Train search error: {str(e)}")
            return []

    def plan_trip(self, user_prompt):
        """
        Plan a trip based on the user's prompt.
        """
        try:
            # Initialize model
            model = genai.GenerativeModel('gemini-1.5-pro')

            # First, ask Gemini to extract travel information from the user query
            extraction_prompt = f"""
            Extract travel information from this user query. Format the response as a JSON object with these fields:
            - origin: The origin city/location
            - destination: The destination city/location for the trip
            - transit_cities: Any cities mentioned for transit (e.g., "I will fly from Delhi" when origin is different)
            - check_in_date: In YYYY-MM-DD format if specified
            - check_out_date: In YYYY-MM-DD format if specified
            - budget: Any budget mentioned, or null if not specified
            - hotel_preference: Any hotel preferences (e.g., "hostel", "5-star", etc.)
            - num_adults: Number of travelers, default to 1 if not specified
            - transportation: Types of transportation mentioned (e.g., "flight", "train", etc.)
            
            User query: {user_prompt}
            
            JSON response:
            """

            response = model.generate_content(extraction_prompt)
            trip_info = {}

            try:
                # Try to parse the JSON response
                json_str = response.text.strip().strip('```json').strip('```').strip()
                trip_info = json.loads(json_str)
                print(f"Extracted trip info: {trip_info}")
            except Exception as e:
                print(f"Error parsing trip info: {str(e)}")
                # Use basic defaults if parsing fails
                trip_info = {
                    "origin": None,
                    "destination": None,
                    "num_adults": 1,
                    "transportation": ["flight"]
                }

            # Perform searches based on extracted information
            search_results = {"prompt": user_prompt}

            # Search for hotels at the destination
            if trip_info.get("destination") and trip_info.get("check_in_date") and trip_info.get("check_out_date"):
                hotel_class = 3  # Default
                if trip_info.get("hotel_preference"):
                    preference = trip_info["hotel_preference"].lower()
                    if "hostel" in preference or "budget" in preference:
                        hotel_class = 2
                    elif "luxury" in preference or "5-star" in preference:
                        hotel_class = 5
                    elif "4-star" in preference:
                        hotel_class = 4

                hotels = self.search_hotels(
                    trip_info["destination"],
                    trip_info["check_in_date"],
                    trip_info["check_out_date"],
                    hotel_class,
                    trip_info.get("num_adults", 1)
                )
                search_results["hotels"] = hotels

            # Search for flights if transportation includes flights
            if trip_info.get("transportation") and "flight" in trip_info["transportation"]:
                # Use transit city as origin for flights if specified
                flight_origin = trip_info.get("transit_cities", [None])[
                    0] or trip_info.get("origin")

                if flight_origin and trip_info.get("destination") and trip_info.get("check_in_date"):
                    flights = self.search_flights(
                        flight_origin,
                        trip_info["destination"],
                        trip_info["check_in_date"],
                        trip_info.get("check_out_date"),
                        trip_info.get("num_adults", 1)
                    )
                    search_results["flights"] = flights

            # Search for trains if transportation includes trains or if origin and transit city specified
            if (trip_info.get("transportation") and "train" in trip_info["transportation"]) or \
               (trip_info.get("origin") and trip_info.get("transit_cities")):
                train_origin = trip_info.get("origin")
                train_destination = trip_info.get("transit_cities", [None])[
                    0] or trip_info.get("destination")

                if train_origin and train_destination and trip_info.get("check_in_date"):
                    trains = self.search_trains(
                        train_origin,
                        train_destination,
                        trip_info["check_in_date"]
                    )
                    search_results["trains"] = trains

            # Search for attractions at the destination
            if trip_info.get("destination"):
                attractions = self.search_attractions(trip_info["destination"])
                search_results["attractions"] = attractions

            # Now, pass all the search results to Gemini for a sassy response
            response_prompt = f"""
            You are TripMate, a sassy but helpful travel assistant with attitude. 
            Your job is to help users plan trips by providing relevant information about destinations, flights, hotels, and attractions.
            
            The user asked: "{user_prompt}"
            
            Based on their request, I've gathered the following information:
            {json.dumps(search_results, indent=2)}
            
            Create a comprehensive travel plan with your signature sassy attitude. Remember:
            - Be witty, sarcastic, and a bit sassy but ultimately helpful
            - Make gentle fun of unrealistic expectations (like low budgets for luxury destinations)
            - Format the information clearly so it's easy to understand
            - Focus on the best 3-5 options for each category
            - Include specific prices, ratings, and practical details
            - If information is missing for any category, acknowledge it with a sassy comment
            - Keep your response concise and to the point
            - If you need more information to provide accurate recommendations, say so clearly

            Today's date for reference is {self.today}.
            """

            response = model.generate_content(response_prompt)
            return response.text

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Detailed error: {error_details}")
            return f"Ugh, something went wrong. Even AI has bad days! Error: {str(e)}"
