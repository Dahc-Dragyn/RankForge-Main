# File: app/agents/digital_asset_generator.py
# Author: MCP Development Core
# Description: The main agent that generates and deploys a 5-page static website.

import os
import uuid
from pathlib import Path
from typing import Optional, Dict

# Import the tools we built
from app.agents.tools.content_generation import generate_page_content_tool
from app.agents.tools.schema_generation import generate_schema_tool
from app.agents.tools.deployment import deploy_to_netlify_tool

# A simple HTML template for all pages
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: sans-serif; line-height: 1.6; padding: 20px; max-width: 800px; margin: auto; }}
        nav a {{ margin-right: 15px; }}
        header, footer {{ text-align: center; padding: 20px 0; }}
    </style>
    {schema_script}
</head>
<body>
    <header>
        <h1>{business_name}</h1>
        <nav>
            <a href="index.html">Home</a>
            <a href="about.html">About Us</a>
            <a href="services.html">Services</a>
            <a href="contact.html">Contact Us</a>
        </nav>
    </header>
    <main>
        {page_content}
    </main>
    <footer>
        <p>&copy; 2025 {business_name}. All Rights Reserved.</p>
    </footer>
</body>
</html>
"""

def generate_content_for_editing(business_name: str, niche: str, location: str) -> dict:
    """
    Generates the initial HTML content for all site pages for user review.
    """
    print(f"--- Stage 1: Generating initial content for '{business_name}' ---")
    
    site_structure = {
        "index.html": {"topic": "Home Page", "title": f"Welcome to {business_name}"},
        "about.html": {"topic": "About Us", "title": f"About {business_name}"},
        "services.html": {"topic": f"Our {niche} Services", "title": f"Our {niche} Services"},
        "contact.html": {"topic": "Contact Us", "title": f"Contact {business_name}"}
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


def assemble_and_deploy_asset(
    business_name: str, 
    niche: str, 
    location: str,
    edited_content: Dict[str, str],
    site_structure: Dict[str, Dict[str, str]],
    netlify_api_key: str,
    site_id: Optional[str] = None # Parameter for re-deploying
) -> dict:
    """
    Assembles the final site from (potentially edited) content and deploys it.
    """
    print(f"--- Stage 2: Assembling and deploying site for '{business_name}' ---")
    
    build_id = str(uuid.uuid4())
    output_dir = Path(f"generated_sites/{build_id}")
    output_dir.mkdir(parents=True, exist_ok=True)

    schema_script = generate_schema_tool(business_name, niche, location)

    for filename, page_info in site_structure.items():
        page_content = edited_content.get(filename, f"<h1>Error: Content for {filename} not found.</h1>")
        
        full_html = HTML_TEMPLATE.format(
            title=page_info["title"],
            schema_script=schema_script if filename == "index.html" else "",
            business_name=business_name,
            page_content=page_content
        )
        with open(output_dir / filename, "w", encoding="utf-8") as f:
            f.write(full_html)
        print(f"  > Assembled {filename}")

    print(f"--- Assembly complete. Starting deployment... ---")
    if not netlify_api_key:
        print("  > SKIPPING DEPLOYMENT: No Netlify API key provided.")
        return {"success": True, "output_path": str(output_dir), "deployment_status": "skipped"}

    # CORRECTED: Pass the site_id to the deployment tool
    deployment_result = deploy_to_netlify_tool(
        directory_path=str(output_dir), 
        netlify_api_key=netlify_api_key,
        site_id=site_id
    )
    
    return {
        "success": True, 
        "output_path": str(output_dir),
        "deployment_result": deployment_result
    }
