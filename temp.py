import os
import json
import logging
import pandas as pd
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="static"), name="static")


# Add session middleware with a secret key
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SESSION_SECRET", "dev_secret_key"))

# Set up Jinja2 templates (assumes your templates are in a folder named 'templates')
templates = Jinja2Templates(directory="templates")

# Load configuration
def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}

def save_config(updated_config):
    try:
        with open('config.json', 'w') as f:
            json.dump(updated_config, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return False

config = load_config()

# Mock functions that would be implemented elsewhere
def get_details(filename):
    logger.debug(f"Getting details for file: {filename}")
    return {
        "rows": 1000,
        "columns": 15,
        "avg_amount": 1250.75,
        "min_amount": 100.25,
        "max_amount": 9999.99,
        "total_records": 1000
    }

def get_summary_table(filename):
    logger.debug(f"Generating summary table for file: {filename}")
    data = {
        "Category": ["Category A", "Category B", "Category C", "Category D", "Category E"],
        "Q1": [100, 150, 200, 120, 180],
        "Q2": [110, 140, 190, 130, 170],
        "Q3": [120, 160, 210, 140, 190],
        "Q4": [130, 170, 220, 150, 200]
    }
    return pd.DataFrame(data)

def get_reason_code(df, filename):
    logger.debug(f"Getting reason codes for file: {filename}")
    return [("Category A", "Q1", 100), ("Category C", "Q3", 210), ("Category E", "Q4", 200)]

def get_top_attributes(engine, selected_cells, contributing_columns, top_n):
    logger.debug(f"Getting top attributes with {len(selected_cells)} selected cells")
    return {
        ("Category A", "Q1", 100): {"Factor 1": 40, "Factor 2": 35, "Factor 3": 25},
        ("Category C", "Q3", 210): {"Factor 4": 70, "Factor 5": 80, "Factor 6": 60},
        ("Category E", "Q4", 200): {"Factor 7": 55, "Factor 8": 90, "Factor 9": 55}
    }

def get_commentary(top_contributors):
    logger.debug(f"Generating commentary based on {len(top_contributors)} contributors")
    return (
        "Based on the analysis, we can observe the following trends:\n\n"
        "1. Cell Category A, Q1 shows lower than expected performance due to Factor 1 (40%), "
        "Factor 2 (35%), and Factor 3 (25%).\n\n"
        "2. Cell Category C, Q3 shows significant growth primarily driven by Factor 5 (80%), "
        "followed by Factor 4 (70%) and Factor 6 (60%).\n\n"
        "3. Cell Category E, Q4 demonstrates strong results with Factor 8 (90%) being the main contributor, "
        "supported by Factor 7 and Factor 9 (both 55%)."
    )

def modify_commentary(user_query, current_commentary):
    logger.debug(f"Modifying commentary based on query: {user_query}")
    return current_commentary + f"\n\nUpdated based on query: {user_query}"

def update_commentary(selected_cells, contributing_columns, top_n):
    logger.debug(f"Updating commentary with {len(selected_cells)} cells, {len(contributing_columns)} columns, top {top_n}")
    top_attrs = get_top_attributes(None, selected_cells, contributing_columns, top_n)
    return get_commentary(top_attrs)

def chat_bot_reply(query):
    logger.debug(f"Generating chatbot reply for: {query}")
    return f"I understand you're asking about '{query}'. This is a system for analyzing financial data. How can I help you understand the current analysis?"

# Routes

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main application page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/files")
async def get_files():
    """Get list of available files"""
    files = ["financial_data_2023.csv", "revenue_report_q2.csv", "expense_analysis.csv"]
    return files

@app.post("/api/file_details")
async def file_details(request: Request):
    """Get details for a specific file"""
    data = await request.json()
    filename = data.get("filename")
    
    if not filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    try:
        details = get_details(filename)
        df = get_summary_table(filename)
        table_data = df.to_dict(orient="records")
        columns = df.columns.tolist()
        selected_cells = get_reason_code(df, filename)
        file_config = config.get(filename, {})
        contributing_columns = file_config.get("contributing_columns", [])
        top_n = file_config.get("top_n", 3)
        top_attrs = get_top_attributes(None, selected_cells, contributing_columns, top_n)
        commentary = get_commentary(top_attrs)
        
        # Save values to session
        request.session["current_file"] = filename
        request.session["summary_table"] = table_data
        request.session["selected_cells"] = selected_cells
        request.session["contributing_columns"] = contributing_columns
        request.session["top_n"] = top_n
        request.session["commentary"] = commentary
        
        return {
            "details": details,
            "table": {
                "data": table_data,
                "columns": columns
            },
            "selected_cells": selected_cells,
            "contributing_columns": contributing_columns,
            "top_n": top_n,
            "commentary": commentary
        }
    
    except Exception as e:
        logger.error(f"Error processing file {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/modify_commentary")
async def api_modify_commentary(request: Request):
    """Modify commentary based on user input"""
    data = await request.json()
    user_query = data.get("query")
    current_commentary = request.session.get("commentary", "")
    
    if not user_query:
        raise HTTPException(status_code=400, detail="No query provided")
    
    try:
        updated_commentary = modify_commentary(user_query, current_commentary)
        request.session["commentary"] = updated_commentary
        return {"commentary": updated_commentary}
    
    except Exception as e:
        logger.error(f"Error modifying commentary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/update_commentary")
async def api_update_commentary(request: Request):
    """Update commentary based on manual settings"""
    data = await request.json()
    selected_cells = data.get("selected_cells", [])
    contributing_columns = data.get("contributing_columns", [])
    top_n = data.get("top_n", 3)
    
    try:
        updated_commentary = update_commentary(selected_cells, contributing_columns, top_n)
        request.session["selected_cells"] = selected_cells
        request.session["contributing_columns"] = contributing_columns
        request.session["top_n"] = top_n
        request.session["commentary"] = updated_commentary
        return {"commentary": updated_commentary}
    
    except Exception as e:
        logger.error(f"Error updating commentary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/save_settings")
async def api_save_settings(request: Request):
    """Save settings to config file"""
    data = await request.json()
    filename = request.session.get("current_file")
    contributing_columns = data.get("contributing_columns", [])
    top_n = data.get("top_n", 3)
    
    if not filename:
        raise HTTPException(status_code=400, detail="No file selected")
    
    try:
        global config
        current_config = load_config()
        current_config[filename] = {
            "contributing_columns": contributing_columns,
            "top_n": top_n
        }
        
        if save_config(current_config):
            config = current_config
            return {"success": True, "message": "Settings saved successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save settings")
    
    except Exception as e:
        logger.error(f"Error saving settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chatbot")
async def api_chatbot(request: Request):
    """Handle chatbot interactions"""
    data = await request.json()
    query = data.get("query")
    
    if not query:
        raise HTTPException(status_code=400, detail="No query provided")
    
    try:
        reply = chat_bot_reply(query)
        return {"reply": reply}
    
    except Exception as e:
        logger.error(f"Error getting chatbot reply: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



# Run the server using uvicorn when executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("your_module_name:app", host="0.0.0.0", port=5000, reload=True)



from fastapi import FastAPI, HTTPException, Depends
from typing import Dict, Any, Optional
import uuid
from pydantic import BaseModel

class InMemorySessionManager:
    """
    Simple in-memory session management for small applications
    Stores session data in a dictionary
    """
    _sessions: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def create_session(cls) -> str:
        """
        Create a new session and return session ID
        """
        session_id = str(uuid.uuid4())
        cls._sessions[session_id] = {}
        return session_id

    @classmethod
    def set(cls, session_id: str, key: str, value: Any):
        """
        Set a value in the session
        """
        if session_id not in cls._sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        cls._sessions[session_id][key] = value

    @classmethod
    def get(cls, session_id: str, key: Optional[str] = None):
        """
        Get a value from the session
        If no key is provided, return entire session data
        """
        if session_id not in cls._sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if key:
            return cls._sessions[session_id].get(key)
        return cls._sessions[session_id]

    @classmethod
    def delete_session(cls, session_id: str):
        """
        Delete a specific session
        """
        if session_id in cls._sessions:
            del cls._sessions[session_id]

# Pydantic model for file details request
class FileDetailsRequest(BaseModel):
    filename: str
    session_id: Optional[str] = None

# FastAPI Application with Session Management
app = FastAPI()

@app.post("/api/file_details")
async def file_details(request: FileDetailsRequest):
    """
    Get details for a specific file with in-memory session management
    """
    filename = request.filename
    
    # Create a new session if no session_id provided
    if not request.session_id:
        session_id = InMemorySessionManager.create_session()
    else:
        session_id = request.session_id
    
    if not filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    try:
        # Your existing file processing logic
        # (Assuming these are imported from your project modules)
        details = get_details(filename)
        df = get_summary_table(filename)
        
        # Convert DataFrame to dict for JSON serialization
        table_data = df.to_dict(orient='records')
        columns = df.columns.tolist()
        
        # Get selected cells
        selected_cells = get_reason_code(df, filename)
        
        # Get default values for this file from config
        file_config = config.get(filename, {})
        contributing_columns = file_config.get('contributing_columns', [])
        top_n = file_config.get('top_n', 3)
        
        # Get top attributes
        top_attrs = get_top_attributes(None, selected_cells, contributing_columns, top_n)
        
        # Generate commentary
        commentary = get_commentary(top_attrs)
        
        # Prepare session data
        session_data = {
            "details": details,
            "table": {
                "data": table_data,
                "columns": columns
            },
            "selected_cells": selected_cells,
            "contributing_columns": contributing_columns,
            "top_n": top_n,
            "commentary": commentary,
            "current_file": filename
        }
        
        # Store entire session data
        InMemorySessionManager.set(session_id, 'file_details', session_data)
        
        # Return response with session ID and data
        return {
            "session_id": session_id,
            **session_data
        }
    
    except Exception as e:
        logger.error(f"Error processing file {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/retrieve_file_details")
async def retrieve_file_details(session_id: str):
    """
    Retrieve previously saved file details
    """
    try:
        # Retrieve session data
        session_data = InMemorySessionManager.get(session_id, 'file_details')
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Session data not found")
        
        return session_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving session data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/delete_session")
async def delete_session(session_id: str):
    """
    Delete a specific session
    """
    try:
        InMemorySessionManager.delete_session(session_id)
        return {"message": "Session deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))