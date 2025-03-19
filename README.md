# TripMate - AI-powered Travel Automation Agent

TripMate is an AI-powered travel assistant designed to help users plan their trips. It leverages Google's Gemini 1.5 Pro AI model and travel APIs to find and recommend flights, hotels, and attractions based on user preferences.

## Features

- **Trip Planning**: Find flights, hotels, and attractions based on your specifications
- **Multi-API Integration**: Connects with travel search APIs to provide up-to-date information
- **Customizable Search**: Specify dates, locations, price ranges, and other preferences
- **Sassy Personality**: Interacts with users in a fun, sassy way while being helpful

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Google Cloud Vertex AI account (for Gemini 1.5 Pro)
- SERP API key (for travel information)

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/TripMate.git
   cd TripMate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env file with your API keys
   ```

### Required Environment Variables

The following environment variables need to be set in your `.env` file:

- `GOOGLE_CLOUD_PROJECT_ID`: Your Google Cloud project ID
- `GOOGLE_CLOUD_LOCATION`: Google Cloud region (default: us-central1)
- `SERP_API_KEY`: Your SERP API key for travel data

### Usage

Run TripMate using the main script:

```bash
python -m tripmate.main
```

When prompted, enter your travel requirements. For example:
- "Find flights from New York to Tokyo for July 15-25"
- "I need a 4-star hotel in Paris near the Eiffel Tower for September 10-15"
- "What are the best attractions to visit in Barcelona?"

## Architecture

TripMate uses a modular architecture with these key components:

- **TripMateAgent**: Core class that handles user queries and coordinates responses
- **API Integration**: Connects to travel APIs through the SERP API service
- **Gemini 1.5 Pro**: Powers the natural language understanding and response generation

### API Functions

TripMate provides these main functions:
- **Hotel Search**: Find hotels based on location, dates, and star rating
- **Flight Search**: Search for flights between destinations on specific dates
- **Attraction Search**: Discover top attractions in any location

## Future Development

- Add support for more travel APIs
- Implement booking functionality
- Create a web interface
- Add support for car rentals and activities

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Vertex AI for Gemini 1.5 Pro capabilities
- SERP API for travel data aggregation
