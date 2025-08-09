# File: app/agents/tools/google_search.py
# Author: MCP Development Core
# Description: A tool for the Market Opportunity Finder agent that performs a Google search.

import os
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def google_search_tool(query: str, num_results: int = 10) -> list:
    """
    Performs a Google search using the Custom Search JSON API and returns
    the top results.

    Args:
        query: The search query string.
        num_results: The number of results to return (max 10).

    Returns:
        A list of search result items, or an empty list if an error occurs.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    # CORRECTED: Removed space from environment variable key
    search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

    if not api_key or not search_engine_id:
        # CORRECTED: Updated error message to reflect the correct key name
        print("Error: GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID must be set in .env")
        return []

    try:
        service = build("customsearch", "v1", developerKey=api_key)
        result = service.cse().list(
            q=query,
            cx=search_engine_id,
            num=num_results
        ).execute()
        return result.get('items', [])
    except HttpError as e:
        print(f"An error occurred during Google Search: {e}")
        return []
    except Exception as e:
        print(f"A non-HTTP error occurred: {e}")
        return []

# This allows us to test the tool directly
if __name__ == '__main__':
    # CORRECTED: Updated function name in the print statement
    print("--- Testing google_search_tool ---")
    test_query = "emergency plumber in Austin"
    # CORRECTED: Called the function with the valid Python name
    results = google_search_tool(test_query)

    if results:
        print(f"Found {len(results)} results for '{test_query}':")
        for i, item in enumerate(results, 1):
            print(f"  {i}. {item['title']}")
            print(f"     Link: {item['link']}")
            print(f"     Snippet: {item.get('snippet', 'N/A').strip()}")
    else:
        print(f"No results found or an error occurred for query: '{test_query}'")