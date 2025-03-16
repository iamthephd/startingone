Core Architecture Blocks
1. Data Ingestion Layer

Video Source Handler: Accepts YouTube URLs or direct video uploads
Transcription Engine:

Uses YouTube Transcript API for YouTube videos
Implements OpenAI Whisper for non-YouTube video content


Timestamp Indexer: Maps transcribed text to precise video timestamps

2. Processing Pipeline

Query Processing Unit: Analyzes and restructures user queries for optimal LLM processing
Primary LLM Engine (Gemini): Identifies candidate segments based on semantic understanding
Refinement LLM Engine: Filters and ranks initial results to improve precision
Context Enrichment Module: Adds surrounding context to improve result relevance

3. Storage Layer

Vector Database: Stores embeddings of transcript segments for semantic searching
Metadata Store: Maintains video information, processed status, and user history
Results Cache: Optimizes performance for repeated queries

4. User Interface Layer

Query Input Interface: User-friendly search interface built with Streamlit
Results Display Module: Shows ranked timestamps with transcript snippets
Video Player Integration: Allows direct navigation to specific timestamps

5. Orchestration Layer

LangChain Framework: Manages the LLM chain interactions
LangGraph Controller: Handles the workflow between multiple LLMs
Performance Monitor: Tracks system performance and response times

Connection Flow

User submits a video URL and search query through the Streamlit interface
Data Ingestion Layer processes the video and generates timestamped transcripts
Transcripts are embedded and stored in the Vector Database
Query Processing Unit formats the user's search request
Primary LLM Engine analyzes the query against the transcript embeddings
Refinement LLM Engine improves result accuracy through additional filtering
Results are ranked and enriched with contextual information
User Interface Layer presents results with navigation options
User can select any timestamp to jump directly to that point in the video