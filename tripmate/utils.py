"""
Utility functions for the TripMate application.
"""

import json
import hashlib
from datetime import datetime, timedelta
from .constants import AIRPORT_CODES


def generate_cache_key(params):
    """Generate a unique cache key based on search parameters."""
    # Convert params dict to a sorted, stringified version for consistent hashing
    param_str = json.dumps(params, sort_keys=True)
    # Create a hash of the parameters
    return hashlib.md5(param_str.encode()).hexdigest()


def get_airport_code(city):
    """Get airport code for city name."""
    if not city:
        return None

    city_lower = city.lower()
    return AIRPORT_CODES.get(city_lower, city_lower)


def make_reasonable_assumptions(memory):
    """Fill in missing details with reasonable assumptions."""
    today = datetime.now()

    # If we have destination but no check-in date, assume two weeks from now
    if memory["destination"] and not memory["check_in_date"]:
        future_date = today + timedelta(days=14)
        memory["check_in_date"] = future_date.strftime('%Y-%m-%d')

    # If we have check-in but no check-out, assume a 7-day stay
    if memory["check_in_date"] and not memory["check_out_date"]:
        check_in = datetime.strptime(memory["check_in_date"], '%Y-%m-%d')
        check_out = check_in + timedelta(days=7)
        memory["check_out_date"] = check_out.strftime('%Y-%m-%d')

    # If we have a destination but no hotel preference, assume 3-star
    if memory["destination"] and not memory["hotel_preference"]:
        memory["hotel_preference"] = "3-star"

    # If we have origin and destination but no transportation, assume flight
    if memory["origin"] and memory["destination"] and not memory["transportation"]:
        memory["transportation"] = ["flight"]

    return memory


def format_duration(duration_minutes):
    """Format duration from minutes to readable format."""
    if not duration_minutes:
        return "Unknown"

    hours = duration_minutes // 60
    minutes = duration_minutes % 60
    return f"{hours}h {minutes}m"


def format_hotel_rating(rating):
    """Format hotel rating to a readable string."""
    if not rating:
        return "No rating"

    # If it's already a string, return it
    if isinstance(rating, str):
        return rating

    # If it's a number, format it with one decimal place
    try:
        return f"{float(rating):.1f}/5.0"
    except (ValueError, TypeError):
        return "Unknown rating"


def format_hotel_reviews(reviews):
    """Format number of reviews to a readable string."""
    if not reviews:
        return "No reviews"

    # If it's already a string, return it
    if isinstance(reviews, str):
        return reviews

    # If it's a number, format it with comma separator
    try:
        return f"{int(reviews):,} reviews"
    except (ValueError, TypeError):
        return "Unknown reviews"
