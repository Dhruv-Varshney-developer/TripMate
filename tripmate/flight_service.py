"""
Flight search service for TripMate.
"""

import time
import requests
from .utils import get_airport_code, generate_cache_key, format_duration


class FlightService:
    """Service for searching and processing flight information."""

    def __init__(self, api_key, cache=None):
        """Initialize flight service with API key and optional cache."""
        self.api_key = api_key
        self.cache = cache or {}

    def search_flights(self, origin, destination, departure_date, return_date=None, adults=1, force_refresh=False):
        """Search for flights using SERP API with correct response parsing."""
        try:
            # Get airport codes if available
            origin_code = get_airport_code(origin)
            dest_code = get_airport_code(destination)

            # Create a params dictionary for cache key generation
            search_params = {
                "origin": origin_code,
                "destination": dest_code,
                "departure_date": departure_date,
                "return_date": return_date,
                "adults": adults
            }

            # Generate cache key
            cache_key = generate_cache_key(search_params)

            # Check if we have cached results and are not forcing a refresh
            if not force_refresh and cache_key in self.cache:
                print(
                    f"\nUsing cached flight results for {origin} to {destination}")
                return self.cache[cache_key]["results"]

            # Base URL for Google Flights search according to SERP API docs
            url = f"https://serpapi.com/search.json?engine=google_flights&departure_id={origin_code}&arrival_id={dest_code}&outbound_date={departure_date}"

            # Add return date if provided
            if return_date:
                url += f"&return_date={return_date}"

            # Add other parameters
            url += f"&currency=USD&hl=en&api_key={self.api_key}"

            print(
                f"\nFlight search URL: {url.replace(self.api_key, 'API_KEY_HIDDEN')}")

            response = requests.get(url)
            data = response.json()

            print(f"\nFlight API response status: {response.status_code}")
            print(
                f"Flight API response keys: {list(data.keys()) if data else 'No data'}")

            # Extract flight information - correctly parse best_flights and other_flights
            flights = []

            # Check best_flights first
            if "best_flights" in data and data["best_flights"]:
                print("Found flights in 'best_flights'")
                # Get top 3 best flights
                for flight_data in data["best_flights"][:3]:
                    # Extract flight details
                    flight_info = {
                        "type": "Best Flight",
                        "price": flight_data.get("price"),
                        "airline": self._extract_airline_name(flight_data),
                        "duration": format_duration(flight_data.get("total_duration")),
                        "stops": self._count_stops(flight_data),
                        "departure_time": self._extract_departure_time(flight_data),
                        "arrival_time": self._extract_arrival_time(flight_data),
                        "layovers": self._extract_layover_info(flight_data)
                    }
                    flights.append(flight_info)

            # Then check other_flights
            if "other_flights" in data and data["other_flights"]:
                print("Found flights in 'other_flights'")
                # Get top 2 other flights
                for flight_data in data["other_flights"][:2]:
                    flight_info = {
                        "type": "Alternative Flight",
                        "price": flight_data.get("price"),
                        "airline": self._extract_airline_name(flight_data),
                        "duration": format_duration(flight_data.get("total_duration")),
                        "stops": self._count_stops(flight_data),
                        "departure_time": self._extract_departure_time(flight_data),
                        "arrival_time": self._extract_arrival_time(flight_data),
                        "layovers": self._extract_layover_info(flight_data)
                    }
                    flights.append(flight_info)

            print(f"Found total of {len(flights)} flights")

            # Cache the results if we found any
            if flights:
                self.cache[cache_key] = {
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

    def _extract_airline_name(self, flight_data):
        """Extract airline name from flight data."""
        if "flights" in flight_data and flight_data["flights"]:
            return flight_data["flights"][0].get("airline", "Unknown")
        return "Unknown"

    def _count_stops(self, flight_data):
        """Count the number of stops in a flight."""
        if "layovers" in flight_data and flight_data["layovers"]:
            return f"{len(flight_data['layovers'])} stop{'s' if len(flight_data['layovers']) > 1 else ''}"
        elif "flights" in flight_data and len(flight_data["flights"]) > 1:
            return f"{len(flight_data['flights']) - 1} stop{'s' if len(flight_data['flights']) > 1 else ''}"
        return "Direct"

    def _extract_departure_time(self, flight_data):
        """Extract departure time from flight data."""
        if "flights" in flight_data and flight_data["flights"]:
            dep_airport = flight_data["flights"][0].get(
                "departure_airport", {})
            if dep_airport and "time" in dep_airport:
                return dep_airport["time"]
        return "Unknown"

    def _extract_arrival_time(self, flight_data):
        """Extract arrival time from flight data."""
        if "flights" in flight_data and flight_data["flights"]:
            flights = flight_data["flights"]
            last_flight = flights[-1]
            arr_airport = last_flight.get("arrival_airport", {})
            if arr_airport and "time" in arr_airport:
                return arr_airport["time"]
        return "Unknown"

    def _extract_layover_info(self, flight_data):
        """Extract layover information from flight data."""
        layover_info = []
        if "layovers" in flight_data and flight_data["layovers"]:
            for layover in flight_data["layovers"]:
                name = layover.get("name", "Unknown Airport")
                duration = layover.get("duration", 0)
                hours = duration // 60
                minutes = duration % 60
                layover_info.append(f"{name} ({hours}h {minutes}m)")
        return layover_info if layover_info else None
