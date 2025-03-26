import uuid
from typing import Dict, Any

class InMemorySessionManager:
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self.current_session_id: str = str(uuid.uuid4())
        self._sessions[self.current_session_id] = {}

    def set(self, key: str, value: Any):
        """Set a value in the current session"""
        self._sessions[self.current_session_id][key] = value

    def get(self, key: str = None):
        """Get a value from the current session"""
        if key:
            return self._sessions[self.current_session_id].get(key)
        return self._sessions[self.current_session_id]

    def create_new_session(self):
        """Create a new session and set it as current"""
        self.current_session_id = str(uuid.uuid4())
        self._sessions[self.current_session_id] = {}
        return self.current_session_id

    def get_current_session_id(self):
        """Get the current active session ID"""
        return self.current_session_id

# Create a global session manager instance
session_manager = InMemorySessionManager()

# FastAPI application
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.post("/api/file_details")
async def file_details(filename: str):
    try:
        # Use the global session manager
        # Store file details in the current session
        details = get_details(filename)
        df = get_summary_table(filename)
        
        # Store data in session
        session_manager.set('file_details', {
            "filename": filename,
            "details": details,
            "table_data": df.to_dict(orient='records')
        })
        
        return {
            "session_id": session_manager.get_current_session_id(),
            "details": details
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/retrieve_file_details")
async def retrieve_file_details():
    try:
        # Retrieve from current session
        file_details = session_manager.get('file_details')
        
        if not file_details:
            raise HTTPException(status_code=404, detail="No file details found")
        
        return file_details
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/new_session")
async def create_new_session():
    """Manually create a new session if needed"""
    new_session_id = session_manager.create_new_session()
    return {"session_id": new_session_id}