# File: app/agents/tools/schema_generation.py
# Author: MCP Development Core
# Description: A tool for generating LocalBusiness JSON-LD schema.

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load all environment variables from the .env file in the project root.
load_dotenv()

def generate_schema_tool(
    business_name: str, 
    niche: str, 
    location: str,
    phone_number: str = "555-555-5555", # Placeholder
    website_url: str = "#" # Placeholder
) -> str:
    """
    Generates LocalBusiness JSON-LD schema markup.

    Args:
        business_name: The name of the business.
        niche: The business niche (e.g., "Roofer", "Landscaper").
        location: The geographic city and state (e.g., "Boise, ID").
        phone_number: The business phone number.
        website_url: The business's website URL.

    Returns:
        A string containing the JSON-LD schema inside a <script> tag.
    """
    print(f"--- Generating LocalBusiness schema for '{business_name}' ---")

    # Construct a detailed prompt for the LLM
    prompt = f"""
    You are a technical SEO expert specializing in structured data. Your task is to generate `LocalBusiness` JSON-LD schema markup.

    **Business Details:**
    - Business Name: {business_name}
    - Business Type/Niche: {niche}
    - Location (City, State): {location}
    - Phone Number: {phone_number}
    - Website URL: {website_url}

    **Instructions:**
    1.  Create a valid JSON-LD object for a `LocalBusiness`.
    2.  Use the `@type` appropriate for the niche (e.g., "RoofingContractor", "Plumber", "Landscaper"). If unsure, use a general type like "ProfessionalService".
    3.  The `address` field should be an `PostalAddress` object with `addressLocality` and `addressRegion` based on the provided location.
    4.  Include the `name`, `telephone`, and `url` fields.
    5.  The final output should be ONLY the complete `<script type="application/ld+json">` tag containing the JSON-LD. Do not add any other text or explanation.
    """

    try:
        # Adhering to the rule of using the most cost-effective model
        model = genai.GenerativeModel('gemini-2.0-flash-lite-001')
        response = model.generate_content(prompt)
        
        # Clean the response to ensure it's just the script tag
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
        return cleaned_response
        
    except Exception as e:
        print(f"An error occurred during schema generation: {e}")
        return f"<!-- Schema generation failed: {e} -->"

# This allows us to test the tool directly
if __name__ == '__main__':
    print("--- Testing generate_schema_tool ---")
    
    test_business_name = "Apex Roofing"
    test_niche = "Roofer"
    test_location = "Boise, ID"
    
    generated_schema = generate_schema_tool(
        business_name=test_business_name,
        niche=test_niche,
        location=test_location
    )

    print("\n--- GENERATED SCHEMA SCRIPT ---")
    print(generated_schema)
