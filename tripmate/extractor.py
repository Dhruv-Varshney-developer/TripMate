"""
Information extraction module for TripMate.
"""

import json
from datetime import date


class TravelInfoExtractor:
    """Extracts travel information from user prompts using LLM."""

    def __init__(self, llm_model):
        """Initialize extractor with LLM model."""
        self.model = llm_model
        self.today = date.today()

    def extract_travel_info(self, user_prompt, current_memory):
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
        {json.dumps(current_memory, indent=2)}
        
        User query: {user_prompt}
        
        JSON response:
        """

        response = self.model.generate_content(extraction_prompt)

        try:
            # Try to parse the JSON response
            json_str = response.text.strip().strip('```json').strip('```').strip()
            new_info = json.loads(json_str)
            print(f"Extracted info: {new_info}")

            # Return new info without updating memory (agent will handle that)
            return new_info

        except Exception as e:
            print(f"Error parsing travel info: {str(e)}")
            # Return empty dict if parsing fails
            return {}

    def update_memory(self, memory, new_info):
        """Update agent memory with new information, preserving existing data."""
        for key, value in new_info.items():
            # Only update if the new value is not None and either:
            # 1. The current value is None, or
            # 2. The new value is different from current (for overriding)
            if value is not None and (memory.get(key) is None or value != memory.get(key)):
                memory[key] = value

        # Special handling for transit_cities as it's a list
        if new_info.get("transit_cities") and isinstance(new_info["transit_cities"], list):
            for city in new_info["transit_cities"]:
                if city and city not in memory["transit_cities"]:
                    memory["transit_cities"].append(city)

        # Special handling for transportation as it's a list
        if new_info.get("transportation") and isinstance(new_info["transportation"], list):
            for mode in new_info["transportation"]:
                if mode and mode not in memory["transportation"]:
                    memory["transportation"].append(mode)

        return memory
