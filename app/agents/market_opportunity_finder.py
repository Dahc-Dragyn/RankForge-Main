# File: app/agents/market_opportunity_finder.py
# Author: MCP Development Core
# Description: The main agent that finds and analyzes market opportunities.

import os
import json
import google.generativeai as genai

# Import the tools we built
from app.agents.tools.google_search import google_search_tool
from app.agents.tools.competitor_analysis import competitor_analysis_tool

# Configure the Gemini API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def analyze_market_opportunity(niche: str, location: str) -> dict:
    """
    Orchestrates the process of finding and analyzing a market opportunity.

    Args:
        niche: The business niche (e.g., "plumber").
        location: The geographic location (e.g., "Austin, TX").

    Returns:
        A dictionary containing the analysis and the final opportunity score.
    """
    print(f"--- Starting analysis for '{niche}' in '{location}' ---")

    # --- Step 1: Use the google_search_tool to find competitors ---
    search_query = f"top {niche}s in {location}"
    competitors = google_search_tool(search_query)
    
    if not competitors:
        return {"error": "Could not find any competitors in the initial Google search."}

    # --- Step 2: Analyze each competitor using the competitor_analysis_tool ---
    analysis_data = []
    print(f"Found {len(competitors)} potential competitors. Analyzing top 5...")
    for competitor in competitors[:5]: # Analyze the top 5 for speed
        url = competitor.get('link')
        if not url:
            continue
        
        print(f"  > Analyzing {url}...")
        on_page_data = competitor_analysis_tool(url)
        if "error" not in on_page_data:
            analysis_data.append(on_page_data)

    if not analysis_data:
        return {"error": "Could not successfully analyze any competitor websites."}

    # --- Step 3: Use Gemini to calculate the Opportunity Score ---
    print("Competitor analysis complete. Preparing data for Gemini...")
    
    # Create the prompt for the LLM
    prompt = f"""
    You are an expert Local SEO Market Analyst. Your task is to calculate a "Digital Desert Opportunity Score" from 0 to 100 for the niche '{niche}' in '{location}'.

    A high score (80-100) means it's a "Digital Desert": an excellent opportunity with weak online competition.
    A low score (0-40) means it's a "Digital Oasis": a saturated market with strong competition.

    Analyze the following on-page SEO data from the top competitors:
    {json.dumps(analysis_data, indent=2)}

    Consider these factors:
    - Titles and H1s: Are they generic or keyword-stuffed? Weak titles like "Home" or "Services" indicate low effort.
    - Meta Descriptions: Are they missing or uncompelling?
    - H2 Headings: Is there a clear, logical structure, or is it sparse?

    Based on your analysis of the data provided, provide a final "Opportunity Score" and a brief "Justification" for your reasoning.
    Return the result as a JSON object with the keys "opportunity_score" and "justification".
    """

    try:
        # CORRECTED: Using the cheapest model as per the new rule.
        model = genai.GenerativeModel('gemini-2.0-flash-lite-001')
        response = model.generate_content(prompt)
        
        # Clean the response to be valid JSON
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
        llm_result = json.loads(cleaned_response)

        return {
            "niche": niche,
            "location": location,
            "opportunity_score": llm_result.get("opportunity_score"),
            "justification": llm_result.get("justification"),
            "competitor_data": analysis_data
        }

    except Exception as e:
        return {"error": f"An error occurred during Gemini analysis: {e}"}


# This allows us to test the agent directly
if __name__ == '__main__':
    test_niche = "roofer"
    test_location = "Boise, ID"
    
    final_analysis = analyze_market_opportunity(test_niche, test_location)

    print("\n--- FINAL ANALYSIS COMPLETE ---")
    if "error" in final_analysis:
        print(f"Error: {final_analysis['error']}")
    else:
        print(f"Niche: {final_analysis['niche']}")
        print(f"Location: {final_analysis['location']}")
        print(f"Opportunity Score: {final_analysis['opportunity_score']}")
        print(f"Justification: {final_analysis['justification']}")
        print("\n--- Raw Competitor Data ---")
        print(json.dumps(final_analysis['competitor_data'], indent=2))