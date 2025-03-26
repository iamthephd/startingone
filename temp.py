import uuid
from typing import Dict, Any

class InMemorySessionManager:
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self.current_session_id: str = str(uuid.uuid4())
        self._sessions[self.current_session_id] = {}
    
    def __getitem__(self, key: str):
        """Allow dictionary-like access to get session data"""
        return self._sessions[self.current_session_id][key]
    
    def __setitem__(self, key: str, value: Any):
        """Allow dictionary-like access to set session data"""
        self._sessions[self.current_session_id][key] = value
    
    def get(self, key: str = None):
        """Get a value from the current session"""
        if key:
            return self._sessions[self.current_session_id].get(key)
        return self._sessions[self.current_session_id]
    
    def set(self, key: str, value: Any):
        """Maintain original set method for backwards compatibility"""
        self._sessions[self.current_session_id][key] = value
    
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

# Example usage
# Now you can do:
# session_manager["file_details"] = {"filename": "example.txt"}
# print(session_manager["file_details"])