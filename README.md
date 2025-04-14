# TripMate - Sassy Travel Assistant

TripMate is a simple AI-powered travel planning assistant with attitude that helps you find flights, hotels, trains, and attractions with a sassy, humorous tone.

## Setup

1. Clone this repository:

   ```bash
   git clone https://github.com/yourusername/tripmate.git
   cd tripmate
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with your API keys:

   ```
   GEMINI_API_KEY=your-gemini-api-key
   SERP_API_KEY=your-serp-api-key
   ```

   Get your API keys from:

   - [Google AI Studio](https://makersuite.google.com/app/apikey) for Gemini API
   - [SerpAPI](https://serpapi.com/) for SERP API

## Usage

Run TripMate from the command line:

```bash
python -m tripmate.main
```

Example queries:

- "I want to travel to Bali from Agra on May 15, 2024. I'll stay for 5 days in a 4-star hotel."
- "Find me flights from Delhi to London on June 10, 2024 and some good hotels."
- "I need to go from Mumbai to Delhi by train on April 20, 2024 and stay for 3 days."
- "Show me the best attractions in Paris, France."

## Notes

- You need to specify dates in your query in YYYY-MM-DD format
- The more details you provide, the better the recommendations

## Learn more about the project on these links:
- [TripMate Planner](https://github.com/Dhruv-Varshney-developer/Tripmate-Planner) - Agent 1
- [TripMate Finder](https://github.com/Dhruv-Varshney-developer/Tripmate-Finder)- Agent 2
- [TripMate Share](https://github.com/Dhruv-Varshney-developer/Tripmate-Share)- Agent 3
- [Technical Whitepaper](https://motley-popcorn-c4a.notion.site/Technical-docs-1d52ab2404df8018afdfe86f4e8fdd29)
- [Tripmate Overview](https://docs.google.com/document/d/1YahKkW0qBaG_6H9lp3DIPhmn56ApjW2dxbJNvrDZqOg/edit?usp=sharing)
- [Demo video](https://www.youtube.com/watch?v=cyKxdZ3uryQ)
- [Presentation Link](https://www.canva.com/design/DAGkjcxFXBQ/az25u5Wo1RgXVDd7d78UYQ/edit?utm_content=DAGkjcxFXBQ&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton) 


## 🚧 Development Note
This project was initially started by importing code from the `browser-use` repository, as we intended to build on top of their library. However, during development, we realized that the library didn’t fulfill our needs, so we removed the original code and rebuilt everything natively from scratch to better align with our goals.


