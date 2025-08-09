# File: app/agents/tools/sanity_tool.py
# Author: MCP Development Core
# Description: A tool for creating and managing content in Sanity.io.

import os
import logging
# CORRECTED: Import the Client from the correct 'sanity.client' module
from sanity.client import Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Basic logging setup for the client
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sanity_tool_create_documents(documents: list) -> dict:
    """
    Creates multiple documents in Sanity.io using a single transaction.

    Args:
        documents: A list of dictionaries, where each dictionary represents a
                   Sanity document to be created.

    Returns:
        A dictionary with the results of the transaction.
    """
    project_id = os.getenv("SANITY_PROJECT_ID")
    api_key = os.getenv("SANITY_API_KEY")
    dataset = "production" # Default dataset name

    if not project_id or not api_key:
        return {"error": "SANITY_PROJECT_ID and SANITY_API_KEY must be set in .env"}

    try:
        # CORRECTED: Initialize the client using the correct class name "Client"
        client = Client(
            logger,
            project_id=project_id,
            dataset=dataset,
            token=api_key,
            use_cdn=False # Use False for mutations to get fresh data
        )
        
        # The transaction logic needs to be a list of mutation objects
        transactions = [{"create": doc} for doc in documents]
            
        result = client.mutate(
            transactions=transactions,
            return_documents=True
        )
        print(f"  > Successfully created {len(documents)} documents in Sanity.")
        return {"success": True, "result": result}

    except Exception as e:
        print(f"An error occurred with the Sanity API: {e}")
        return {"error": str(e)}

# This allows us to test the tool directly
if __name__ == '__main__':
    print("--- Testing sanity_tool_create_documents ---")
    
    # Create some dummy page documents to upload
    test_documents = [
        {
            "_type": "page",
            "title": "Home",
            "slug": {"_type": "slug", "current": "home"},
            "content": "<h1>Welcome to the Test Site!</h1><p>This is the homepage content.</p>"
        },
        {
            "_type": "page",
            "title": "About Us",
            "slug": {"_type": "slug", "current": "about"},
            "content": "<h2>About Our Company</h2><p>We are a test company doing test things.</p>"
        }
    ]
    
    result = sanity_tool_create_documents(test_documents)
    print("\n--- SANITY.IO API RESPONSE ---")
    print(result)
