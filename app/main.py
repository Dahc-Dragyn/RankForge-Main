# File: app/main.py
# Author: MCP Development Core
# Description: Main entry point for the Local Arbitrage MCP Server.

import uuid
from typing import Dict, Any
from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from firebase_admin import firestore

# Import our security function
from app.security.authentication import get_current_user

# Import our agent functions
from app.agents.market_opportunity_finder import analyze_market_opportunity
from app.agents.digital_asset_generator import generate_content_for_editing, assemble_and_push_to_cms

# --- App Configuration ---
app = FastAPI(
    title="Local Arbitrage MCP Server",
    description="The central system for finding Digital Deserts and generating high-performing digital assets.",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
db = firestore.client()

# --- Pydantic Models for Data Validation ---
class AnalysisRequest(BaseModel):
    niche: str
    location: str

class ContentGenerationRequest(BaseModel):
    business_name: str
    niche: str
    location: str

class AssemblyRequest(BaseModel):
    business_name: str
    niche: str
    location: str
    edited_content: Dict[str, str]
    site_structure: Dict[str, Dict[str, str]]

class UserSettings(BaseModel):
    netlify_api_key: str # This can be expanded later to include Sanity keys if needed

# --- In-memory storage for background task status ---
cms_push_tasks = {}

def run_cms_push_task(task_id: str, user_id: str, request_data: dict):
    """A wrapper function that runs the agent to push content to the CMS."""
    try:
        result = assemble_and_push_to_cms(
            business_name=request_data['business_name'],
            niche=request_data['niche'],
            location=request_data['location'],
            edited_content=request_data['edited_content'],
            site_structure=request_data['site_structure']
        )
        
        # --- THIS IS THE FIX ---
        # If the push to Sanity was successful, save a record to Firestore.
        if result.get("success"):
            sanity_results = result.get("sanity_result", {}).get("result", {}).get("results", [])
            if sanity_results:
                # Use the first document ID from the Sanity result as our site ID
                site_id = sanity_results[0].get("document", {}).get("_id")
                if site_id:
                    site_doc_ref = db.collection('users').document(user_id).collection('sites').document(site_id)
                    site_doc_ref.set({
                        "business_name": request_data['business_name'],
                        "niche": request_data['niche'],
                        "location": request_data['location'],
                        "sanity_site_id": site_id, # Store the Sanity ID
                        "content": request_data['edited_content'],
                        "site_structure": request_data['site_structure'],
                        "last_updated": firestore.SERVER_TIMESTAMP
                    }, merge=True)

        cms_push_tasks[task_id] = {"status": "complete", "result": result}
    except Exception as e:
        cms_push_tasks[task_id] = {"status": "failed", "error": str(e)}


# --- HTML Serving Endpoint ---
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    """Serves the main index.html file as the root page."""
    return templates.TemplateResponse("index.html", {"request": request})


# --- Protected API Endpoints (v1) ---
@app.post("/api/v1/generate-content")
def generate_initial_content(request: ContentGenerationRequest, user: dict = Depends(get_current_user)):
    """Generates the initial AI content for all pages and returns it for editing."""
    return generate_content_for_editing(
        business_name=request.business_name,
        niche=request.niche,
        location=request.location
    )

@app.post("/api/v1/assemble-and-deploy", status_code=status.HTTP_202_ACCEPTED)
def start_assembly_and_push(
    request: AssemblyRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    """
    Starts a background task to assemble content and push it to the Headless CMS.
    """
    user_id = user["uid"]
    task_id = str(uuid.uuid4())
    cms_push_tasks[task_id] = {"status": "in_progress"}
    
    background_tasks.add_task(run_cms_push_task, task_id, user_id, request.dict())
    
    return {"message": "Content push to CMS started.", "task_id": task_id}

@app.get("/api/v1/deployment-status/{task_id}")
def get_push_status(task_id: str, user: dict = Depends(get_current_user)):
    """Polls for the status of a background CMS push task."""
    task = cms_push_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

# --- Other Endpoints (Largely Unchanged) ---
@app.get("/api/v1/sites")
def get_user_sites(user: dict = Depends(get_current_user)):
    """Retrieves a list of all sites for the current user."""
    user_id = user["uid"]
    sites_ref = db.collection('users').document(user_id).collection('sites')
    sites = []
    for doc in sites_ref.stream():
        site_data = doc.to_dict()
        # We don't need to send the full content in the list view
        site_data.pop('content', None) 
        site_data.pop('site_structure', None)
        sites.append(site_data)
    return sites

@app.get("/api/v1/sites/{site_id}")
def get_site_details(site_id: str, user: dict = Depends(get_current_user)):
    """Retrieves the full details, including content, for a specific site."""
    user_id = user["uid"]
    doc_ref = db.collection('users').document(user_id).collection('sites').document(site_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Site not found")
    return doc.to_dict()

@app.get("/api/v1/me")
def get_user_profile(user: dict = Depends(get_current_user)):
    return {"message": "Authenticated successfully!", "user_data": user}

@app.post("/api/v1/user/settings")
def save_user_settings(settings: UserSettings, user: dict = Depends(get_current_user)):
    user_id = user["uid"]
    db.collection('users').document(user_id).set({'netlify_api_key': settings.netlify_api_key}, merge=True)
    return {"message": "Settings saved successfully."}

@app.get("/api/v1/user/settings")
def get_user_settings(user: dict = Depends(get_current_user)):
    user_id = user["uid"]
    doc = db.collection('users').document(user_id).get()
    return doc.to_dict() if doc.exists else {}

@app.post("/api/v1/analyze")
def run_market_analysis(request: AnalysisRequest, user: dict = Depends(get_current_user)):
    return analyze_market_opportunity(niche=request.niche, location=request.location)
