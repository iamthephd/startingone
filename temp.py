from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
import os
import pandas as pd
from pydantic import BaseModel
from typing import List, Dict, Optional

# Assuming these are imported from your existing project
# You'll need to implement these functions similarly to your Flask version
from your_project_modules import (
    load_config, 
    get_details, 
    get_summary_table, 
    get_reason_code, 
    get_top_attributes, 
    get_commentary, 
    modify_commentary, 
    update_commentary, 
    save_config,
    chat_bot_reply,
    logger
)

app = FastAPI()

# Setup templates (if you're using server-side rendering)
templates = Jinja2Templates(directory="templates")

# Load configuration
config = load_config()

# Pydantic models for request validation
class FileDetailsRequest(BaseModel):
    filename: str

class ModifyCommentaryRequest(BaseModel):
    query: str

class UpdateCommentaryRequest(BaseModel):
    selected_cells: List[Dict] = []
    contributing_columns: List[str] = []
    top_n: int = 3

class SaveSettingsRequest(BaseModel):
    contributing_columns: List[str] = []
    top_n: int = 3

class ChatbotRequest(BaseModel):
    query: str

@app.get("/")
async def index(request: Request):
    """Main application page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/files")
async def get_files():
    """Get list of available files"""
    # This would typically come from a database or filesystem
    files = ["financial_data_2023.csv", "revenue_report_q2.csv", "expense_analysis.csv"]
    return files

@app.post("/api/file_details")
async def file_details(request: FileDetailsRequest):
    """Get details for a specific file"""
    filename = request.filename
    
    if not filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    try:
        # Get file details
        details = get_details(filename)
        
        # Get summary table
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
async def api_modify_commentary(request: ModifyCommentaryRequest):
    """Modify commentary based on user input"""
    user_query = request.query
    
    if not user_query:
        raise HTTPException(status_code=400, detail="No query provided")
    
    try:
        # Call modify_commentary function
        # Note: In FastAPI, you'll need to manage state differently 
        # (e.g., using database or external storage instead of session)
        current_commentary = ""  # You'll need to retrieve this from your state management
        updated_commentary = modify_commentary(user_query, current_commentary)
        
        return {"commentary": updated_commentary}
    
    except Exception as e:
        logger.error(f"Error modifying commentary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/update_commentary")
async def api_update_commentary(request: UpdateCommentaryRequest):
    """Update commentary based on manual settings"""
    try:
        # Call update_commentary function
        updated_commentary = update_commentary(
            request.selected_cells, 
            request.contributing_columns, 
            request.top_n
        )
        
        return {"commentary": updated_commentary}
    
    except Exception as e:
        logger.error(f"Error updating commentary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/save_settings")
async def api_save_settings(request: SaveSettingsRequest):
    """Save settings to config file"""
    try:
        # Get current filename (you'll need to implement state management)
        filename = ""  # Retrieve current filename from your state management
        
        if not filename:
            raise HTTPException(status_code=400, detail="No file selected")
        
        # Update config
        current_config = load_config()
        current_config[filename] = {
            'contributing_columns': request.contributing_columns,
            'top_n': request.top_n
        }
        
        # Save config
        if save_config(current_config):
            return {"success": True, "message": "Settings saved successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save settings")
    
    except Exception as e:
        logger.error(f"Error saving settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chatbot")
async def api_chatbot(request: ChatbotRequest):
    """Handle chatbot interactions"""
    query = request.query
    
    if not query:
        raise HTTPException(status_code=400, detail="No query provided")
    
    try:
        # Get chatbot reply
        reply = chat_bot_reply(query)
        
        return {"reply": reply}
    
    except Exception as e:
        logger.error(f"Error getting chatbot reply: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000)