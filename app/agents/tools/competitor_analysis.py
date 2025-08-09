# File: app/agents/tools/competitor_analysis.py
# Author: MCP Development Core
# Description: A tool for scraping and analyzing a competitor's on-page SEO.

import httpx
from bs4 import BeautifulSoup

def competitor_analysis_tool(url: str) -> dict:
    """
    Scrapes a given URL and extracts key on-page SEO elements.

    Args:
        url: The URL of the competitor's page to analyze.

    Returns:
        A dictionary containing the page title, meta description, H1, and H2 headings.
        Returns a dictionary with an 'error' key if scraping fails.
    """
    # Set a user-agent to mimic a real browser visit
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        with httpx.Client(headers=headers, follow_redirects=True, timeout=10.0) as client:
            response = client.get(url)
            # Raise an exception for bad status codes (4xx or 5xx)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract key SEO elements
        title = soup.find('title').get_text(strip=True) if soup.find('title') else 'N/A'
        
        meta_description_tag = soup.find('meta', attrs={'name': 'description'})
        meta_description = meta_description_tag['content'].strip() if meta_description_tag else 'N/A'
        
        h1 = soup.find('h1').get_text(strip=True) if soup.find('h1') else 'N/A'
        
        h2s = [h2.get_text(strip=True) for h2 in soup.find_all('h2')]

        return {
            "url": url,
            "title": title,
            "meta_description": meta_description,
            "h1": h1,
            "h2s": h2s
        }

    except httpx.RequestError as e:
        return {"error": f"HTTP request failed: {e.__class__.__name__}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e.__class__.__name__}"}

# This allows us to test the tool directly
if __name__ == '__main__':
    print("--- Testing competitor_analysis_tool ---")
    # Using a URL from our previous search results
    test_url = "https://www.abacusplumbing.com/plumbing/"
    
    analysis_results = competitor_analysis_tool(test_url)

    if "error" in analysis_results:
        print(f"Failed to analyze {test_url}:")
        print(f"  Error: {analysis_results['error']}")
    else:
        print(f"Successfully analyzed {test_url}:")
        print(f"  Title: {analysis_results['title']}")
        print(f"  Meta Description: {analysis_results['meta_description']}")
        print(f"  H1: {analysis_results['h1']}")
        print(f"  H2s Found ({len(analysis_results['h2s'])}):")
        for h2 in analysis_results['h2s']:
            print(f"    - {h2}")