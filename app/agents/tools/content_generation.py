# File: app/agents/tools/content_generation.py
# Author: MCP Development Core
# Description: A tool for generating localized, keyword-informed page content.

import os
import google.generativeai as genai
# CORRECTED: Explicitly import and call load_dotenv to ensure environment is set.
from dotenv import load_dotenv

# Load all environment variables from the .env file in the project root.
load_dotenv()

def generate_page_content_tool(
    business_name: str, 
    niche: str, 
    location: str, 
    page_topic: str, 
    keywords: list = None
) -> str:
    """
    Generates a full page of content for a specific topic using the Gemini API.

    Args:
        business_name: The name of the fictional business.
        niche: The business niche (e.g., "Roofer", "Landscaper").
        location: The geographic location (e.g., "Boise, ID").
        page_topic: The specific topic of the page (e.g., "Home", "About Us", "Roof Repair Services").
        keywords: An optional list of keywords to naturally include in the content.

    Returns:
        A string containing the generated page content in HTML format.
    """
    print(f"--- Generating content for '{page_topic}' page for '{business_name}' ---")

    # Construct a detailed prompt for the LLM
    prompt = f"""
    You are an expert local SEO copywriter. Your task is to write the complete content for a webpage.

    **Business Details:**
    - Business Name: {business_name}
    - Niche: {niche}
    - Location: {location}

    **Page Topic:** {page_topic}

    **Instructions:**
    1.  Write in a professional, trustworthy, and customer-focused tone.
    2.  The content should be at least 400 words long.
    3.  Start with a compelling `<h1>` heading that is relevant to the page topic.
    4.  Structure the content with multiple `<h2>` subheadings.
    5.  Write clear and informative paragraphs under each subheading.
    6.  Naturally weave the business name, niche, and location throughout the text.
    7.  If keywords are provided, incorporate them naturally. Keywords: {keywords if keywords else 'N/A'}.
    8.  End with a clear Call to Action, encouraging visitors to call or fill out a form.
    9.  The final output should be ONLY the raw HTML content for the page body, starting with the `<h1>` tag. Do not include `<html>`, `<head>`, or `<body>` tags.
    """

    try:
        # Adhering to the rule of using the most cost-effective model
        model = genai.GenerativeModel('gemini-2.0-flash-lite-001')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"An error occurred during content generation: {e}")
        return f"<h1>Error Generating Content</h1><p>An error occurred while trying to generate content for the {page_topic} page.</p>"

# This allows us to test the tool directly
if __name__ == '__main__':
    print("--- Testing generate_page_content_tool ---")
    
    test_business_name = "Apex Roofing"
    test_niche = "Roofer"
    test_location = "Boise, ID"
    test_page_topic = "Emergency Roof Repair"
    
    generated_html = generate_page_content_tool(
        business_name=test_business_name,
        niche=test_niche,
        location=test_location,
        page_topic=test_page_topic
    )

    print("\n--- GENERATED HTML CONTENT ---")
    print(generated_html)
