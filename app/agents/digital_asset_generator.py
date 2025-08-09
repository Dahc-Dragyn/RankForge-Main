# File: app/agents/digital_asset_generator.py
# Author: MCP Development Core
# Description: The main agent that generates and pushes content to a headless CMS.

import os
from typing import Optional, Dict

# Import the tools we built
from app.agents.tools.content_generation import generate_page_content_tool
# CORRECTED: Import the new Sanity.io tool
from app.agents.tools.sanity_tool import sanity_tool_create_documents


def generate_content_for_editing(business_name: str, niche: str, location: str) -> dict:
    """
    Generates the initial HTML content for all site pages for user review.
    """
    print(f"--- Stage 1: Generating initial content for '{business_name}' ---")
    
    site_structure = {
        "index.html": {"topic": "Home Page", "title": "Home"},
        "about.html": {"topic": "About Us", "title": "About Us"},
        "services.html": {"topic": f"Our {niche} Services", "title": "Services"},
        "contact.html": {"topic": "Contact Us", "title": "Contact Us"}
    }
    
    generated_content = {}
    for filename, page_info in site_structure.items():
        content = generate_page_content_tool(
            business_name=business_name,
            niche=niche,
            location=location,
            page_topic=page_info["topic"]
        )
        generated_content[filename] = content
        print(f"  > Generated content for {filename}")

    return {"success": True, "content": generated_content, "site_structure": site_structure}


def assemble_and_push_to_cms(
    business_name: str, 
    niche: str, 
    location: str,
    edited_content: Dict[str, str],
    site_structure: Dict[str, Dict[str, str]]
) -> dict:
    """
    Assembles the final content into Sanity.io documents and pushes them to the CMS.
    """
    print(f"--- Stage 2: Assembling and pushing content to Sanity.io for '{business_name}' ---")
    
    # --- Step 1: Format the content into Sanity document structure ---
    documents_to_create = []
    for filename, content in edited_content.items():
        page_info = site_structure.get(filename, {})
        slug = filename.replace('.html', '')
        
        document = {
            "_type": "page", # Assumes a 'page' schema in Sanity
            "title": page_info.get("title", slug.capitalize()),
            "slug": {"_type": "slug", "current": slug},
            "content": content, # The user-edited HTML content
            "businessName": business_name, # Storing metadata for context
            "niche": niche,
            "location": location
        }
        documents_to_create.append(document)
    
    print(f"  > Prepared {len(documents_to_create)} documents for Sanity.")

    # --- Step 2: Push the documents to Sanity.io using our tool ---
    sanity_result = sanity_tool_create_documents(documents_to_create)

    if sanity_result.get("error"):
        return {"success": False, "error": sanity_result["error"]}

    print(f"--- Content push to Sanity.io complete. ---")
    return {
        "success": True,
        "sanity_result": sanity_result
    }

