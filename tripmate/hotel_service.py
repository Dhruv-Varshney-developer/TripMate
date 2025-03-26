"""
Hotel search service for TripMate.
"""

import time
import requests
from .utils import generate_cache_key, format_hotel_rating, format_hotel_reviews


class HotelService:
    """Service for searching and processing hotel information."""

    def __init__(self, api_key, cache=None):
        """Initialize hotel service with API key and optional cache."""
        self.api_key = api_key
        self.cache = cache or {}

    def search_hotels(self, location, check_in_date, check_out_date, adults=1, force_refresh=False):
        """Search for hotels using SERP API with correct response parsing."""
        try:
            # Create a params dictionary for cache key generation
            search_params = {
                "location": location,
                "check_in_date": check_in_date,
                "check_out_date": check_out_date,
                "adults": adults
            }

            # Generate cache key
            cache_key = generate_cache_key(search_params)

            # Check if we have cached results and are not forcing a refresh
            if not force_refresh and cache_key in self.cache:
                print(f"\nUsing cached hotel results for {location}")
                return self.cache[cache_key]["results"]

            # Format the query string properly
            query = f"{location} Hotels"
            query_encoded = requests.utils.quote(query)

            # Build URL according to SERP API docs
            url = f"https://serpapi.com/search.json?engine=google_hotels&q={query_encoded}&check_in_date={check_in_date}&check_out_date={check_out_date}&adults={adults}&currency=USD&gl=us&hl=en&api_key={self.api_key}"

            print(
                f"\nHotel search URL: {url.replace(self.api_key, 'API_KEY_HIDDEN')}")

            response = requests.get(url)
            data = response.json()

            print(f"\nHotel API response status: {response.status_code}")
            print(
                f"Hotel API response keys: {list(data.keys()) if data else 'No data'}")

            # Extract the most relevant hotel information
            hotels = []
            if "properties" in data:
                for hotel in data["properties"][:5]:  # Limit to top 5 hotels
                    # Extract price information
                    price_info = self._extract_hotel_price(hotel)

                    # Create hotel object with all available details
                    hotel_info = {
                        "name": hotel.get("name", "Unknown"),
                        "price": price_info.get("total_price", hotel.get("price", "Unknown")),
                        "price_per_night": price_info.get("per_night", "Unknown"),
                        "rating": format_hotel_rating(hotel.get("rating")),
                        "reviews": format_hotel_reviews(hotel.get("reviews")),
                        "stars": hotel.get("stars", "Unknown"),
                        "location": hotel.get("address", "Unknown"),
                        "thumbnail": hotel.get("thumbnail", None),
                        "link": hotel.get("link", None),
                        "description": self._extract_hotel_description(hotel),
                        "amenities": hotel.get("amenities", [])
                    }

                    # Filter out None or "Unknown" values
                    hotel_info = {k: v for k, v in hotel_info.items() if v not in [
                        None, "Unknown", "", []]}

                    hotels.append(hotel_info)

                print(f"Found {len(hotels)} hotels")

                # Cache the results
                self.cache[cache_key] = {
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

    def _extract_hotel_price(self, hotel):
        """Extract detailed price information from hotel data."""
        price_info = {}

        # Try to get the total price for the stay
        if "price" in hotel:
            price_info["total_price"] = hotel["price"]

        # Try to get price per night if available
        if "price_description" in hotel:
            desc = hotel["price_description"]
            if isinstance(desc, str) and "per night" in desc.lower():
                # Extract the per night price from description
                price_info["per_night"] = desc

        return price_info

    def _extract_hotel_description(self, hotel):
        """Extract a description of the hotel from available data."""
        description = []

        # Add hotel type if available
        if "type" in hotel:
            description.append(hotel["type"])

        # Add highlighted amenities if available
        if "highlight" in hotel:
            description.append(hotel["highlight"])

        # Join all parts with commas
        return ", ".join(description) if description else None
