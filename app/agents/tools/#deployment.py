# File: app/agents/tools/deployment.py
# Author: MCP Development Core
# Description: A tool for deploying a static site to Netlify.

import os
import json
import hashlib
import mimetypes
import uuid
from pathlib import Path
from typing import Optional
import httpx
from dotenv import load_dotenv

load_dotenv()

NETLIFY_API_BASE = "https://api.netlify.com/api/v1"

def _calculate_sha1(filepath: Path) -> str:
    """Calculates the SHA1 hash of a file."""
    sha1 = hashlib.sha1()
    with open(filepath, 'rb') as f:
        while True:
            data = f.read(65536)
            if not data:
                break
            sha1.update(data)
    return sha1.hexdigest()

def deploy_to_netlify_tool(
    directory_path: str, 
    netlify_api_key: str,
    site_id: Optional[str] = None # Added optional site_id for re-deployments
) -> dict:
    """
    Deploys a directory of static files to Netlify. If a site_id is provided,
    it updates the existing site. Otherwise, it creates a new one.
    """
    if not netlify_api_key:
        return {"error": "Netlify API key is missing."}

    headers = {"Authorization": f"Bearer {netlify_api_key}"}
    site_dir = Path(directory_path)

    try:
        with httpx.Client(headers=headers, timeout=60.0) as client:
            # --- Step 1: Prepare file manifest ---
            files_to_upload = {}
            for filepath in site_dir.rglob('*'):
                if filepath.is_file():
                    rel_path = f"/{filepath.relative_to(site_dir).as_posix()}"
                    files_to_upload[rel_path] = _calculate_sha1(filepath)
            
            # --- Step 2: Create a new site OR use existing site_id ---
            if not site_id:
                print("  > No site_id provided. Creating a new site on Netlify...")
                site_creation_payload = {"name": f"mcp-asset-{uuid.uuid4().hex[:8]}"}
                response = client.post(f"{NETLIFY_API_BASE}/sites", json=site_creation_payload)
                response.raise_for_status()
                site_data = response.json()
                site_id = site_data['id']
                print(f"  > Successfully created Netlify site: {site_id}")
            else:
                print(f"  > Existing site_id provided ({site_id}). Fetching site data...")
                response = client.get(f"{NETLIFY_API_BASE}/sites/{site_id}")
                response.raise_for_status()
                site_data = response.json()

            # --- Step 3: Create a new deploy for the site ---
            deploy_payload = {"files": files_to_upload}
            response = client.post(f"{NETLIFY_API_BASE}/sites/{site_id}/deploys", json=deploy_payload)
            response.raise_for_status()
            deploy_data = response.json()
            deploy_id = deploy_data['id']
            required_files = deploy_data.get('required', [])
            print(f"  > Created deploy {deploy_id}. Required files: {len(required_files)}")

            # --- Step 4: Upload required files ---
            for sha in required_files:
                filepath_to_upload = next((p for p, s in files_to_upload.items() if s == sha), None)
                if filepath_to_upload:
                    print(f"    - Uploading {filepath_to_upload}...")
                    file_content = (site_dir / filepath_to_upload.lstrip('/')).read_bytes()
                    upload_headers = {
                        "Authorization": f"Bearer {netlify_api_key}",
                        "Content-Type": mimetypes.guess_type(filepath_to_upload)[0] or 'application/octet-stream'
                    }
                    upload_url = f"{NETLIFY_API_BASE}/deploys/{deploy_id}/files{filepath_to_upload}"
                    
                    with httpx.Client() as upload_client:
                         upload_response = upload_client.put(upload_url, content=file_content, headers=upload_headers)
                         upload_response.raise_for_status()

        print(f"--- Deployment successful! Site URL: {site_data['ssl_url']} ---")
        return {
            "success": True,
            "site_id": site_id,
            "deploy_id": deploy_id,
            "url": site_data['ssl_url']
        }

    except httpx.RequestError as e:
        return {"error": f"HTTP request failed: {e.__class__.__name__} - {e.request.url}"}
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP Error: {e.response.status_code} - {e.response.text}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}

