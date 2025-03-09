# TripMate - AI-powered Travel Automation Agent

TripMate is an AI-powered travel automation agent designed to streamline the travel planning and booking process. It leverages browser automation to search for and book travel arrangements based on user preferences.

## Features

- **Travel Data Processing**: Analyzes user travel requirements and preferences
- **Website Selection**: Identifies the best travel websites based on user criteria
- **Ticket Booking Automation**: Automates the process of booking flights, hotels, etc. (excluding payment)
- **Invoice Generation**: Creates detailed invoices for completed bookings

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Playwright (for browser automation)

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

3. Install Playwright:
   ```bash
   playwright install
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env file with your API keys
   ```

### Usage

Run TripMate using the main script:

```bash
python main.py
```

When prompted, enter your travel requirements. For example:
- "Find a round-trip flight from New York to Tokyo for July 15-25"
- "Book a hotel in Paris near the Eiffel Tower for September 10-15"

## Architecture

TripMate is built on top of the [browser-use](https://github.com/browser-use/browser-use) library for robust browser control. It integrates Large Language Models (LLMs) for decision-making and intelligent interaction with travel websites.

The main components are:
- **Agent**: Coordinates the overall automation process
- **Browser Controller**: Handles browser interaction and navigation
- **Invoice Generator**: Creates standardized invoices for bookings

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [browser-use](https://github.com/browser-use/browser-use) for browser automation capabilities
- OpenAI for language model capabilities
