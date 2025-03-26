from fastapi import FastAPI, Request, HTTPException
from typing import Optional, Dict, Any
import uuid

class InMemorySessionManager:
    """
    Simple in-memory session management for small applications
    """
    _sessions: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def create_session(cls) -> str:
        """Create a new session and return session ID"""
        session_id = str(uuid.uuid4())
        cls._sessions[session_id] = {}
        return session_id

    @classmethod
    def set(cls, session_id: str, key: str, value: Any):
        """Set a value in the session"""
        if session_id not in cls._sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        cls._sessions[session_id][key] = value

    @classmethod
    def get(cls, session_id: str, key: Optional[str] = None):
        """Get a value from the session"""
        if session_id not in cls._sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if key:
            return cls._sessions[session_id].get(key)
        return cls._sessions[session_id]