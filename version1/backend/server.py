import os
import json
import yaml
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import sys
import logging
from functools import lru_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.database_process import create_oracle_engine
from backend.database.get_summary_table import *
from backend.database.get_top_contributors import get_top_attributes_by_difference
from backend.llm.reson_code import get_reason_code
from backend.llm.commentary import get_commentary, modify_commentary
from backend.llm.chatbot import process_chatbot_query
from backend.utils.helper import read_config, get_file_config_by_path, convert_to_int, format_top_contributors

app = Flask(__name__)
CORS(app, supports_credentials=True)  # Enable CORS with credentials support

# Configuration
CONFIG_FILE = "config/config.yaml"
EXCEL_DATA_PATH = "data"

# Load configuration once
config = read_config(CONFIG_FILE)

# Initialize database engine once at startup
db_config = config.get('database', {})
engine = None

def get_engine():
    """Get or create the database engine"""
    global engine
    if engine is None:
        logger.info("Creating new database engine connection")
        try:
            engine = create_oracle_engine(db_config)
            logger.info("Database engine created successfully")
        except Exception as e:
            logger.error(f"Failed to create database engine: {str(e)}")
            raise
    return engine

# Cache file configs to reduce disk reads
@lru_cache(maxsize=32)
def get_cached_file_config(file_name):
    """Get configuration for a specific file with caching"""
    try:
        return get_file_config_by_path(config, file_name)
    except Exception as e:
        logger.error(f"Error getting file config for {file_name}: {str(e)}")
        raise

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify server is running"""
    try:
        # Test database connection
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute("SELECT 1 FROM DUAL")
        return jsonify({'status': 'healthy'})
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/api/files', methods=['GET'])
def get_files():
    """Get list of available Excel files"""
    try:
        excel_files = [f for f in os.listdir(EXCEL_DATA_PATH) if f.endswith('.xlsx')]
        return jsonify({'files': excel_files})
    except Exception as e:
        logger.error(f"Error getting files: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/file-config/<file_name>', methods=['GET'])
def get_file_config(file_name):
    """Get configuration for a specific file"""
    try:
        file_config = get_cached_file_config(file_name)
        return jsonify(file_config)
    except Exception as e:
        logger.error(f"Error getting file config: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/summary-table/<file_name>', methods=['GET'])
def get_summary_table(file_name):
    """Get summary table data for a file"""
    try:
        file_config = get_cached_file_config(file_name)
        summary_func_name = file_config.get('summary_table_function')
        
        if not summary_func_name or summary_func_name not in globals():
            logger.error(f"Summary function {summary_func_name} not found")
            return jsonify({'error': f'Summary function {summary_func_name} not found'}), 404
        
        summary_func = globals()[summary_func_name]
        
        # Get the engine
        engine = get_engine()
        
        df = summary_func(engine)
        df = df.map(convert_to_int)
        
        # Check if these columns exist before dropping
        columns_to_drop = []
        for col in ['Y/Y %', 'Q/Q %']:
            if col in df.columns:
                columns_to_drop.append(col)
        
        if columns_to_drop:
            df = df.drop(columns=columns_to_drop)
        
        # Convert DataFrame to JSON
        result = {
            'data': df.to_dict(orient='records'),
            'index': df.index.tolist()
        }
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting summary table: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reason-code/<file_name>', methods=['POST'])
def get_reason_code_api(file_name):
    """Get reason code for a file"""
    try:
        data = request.json
        df_json = data.get('df')
        df = pd.read_json(df_json, orient='split')
        
        selected_cells = get_reason_code(df, file_name)
        return jsonify({'selected_cells': selected_cells})
    except Exception as e:
        logger.error(f"Error getting reason code: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/top-contributors/<file_name>', methods=['POST'])
def get_top_contributors_api(file_name):
    """Get top contributors for selected cells"""
    try:
        data = request.json
        selected_cells = data.get('selected_cells')
        contributing_columns = data.get('contributing_columns')
        top_n = data.get('top_n')
        
        file_config = get_cached_file_config(file_name)
        table_name = file_config.get('table_name')
        
        engine = get_engine()
        
        top_contributors = get_top_attributes_by_difference(
            engine,
            selected_cells,
            table_name,
            contributing_columns,
            top_n
        )
        
        top_contributors_formatted = format_top_contributors(top_contributors)
        return jsonify({'contributors': top_contributors_formatted})
    except Exception as e:
        logger.error(f"Error getting top contributors: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/commentary/<file_name>', methods=['POST'])
def get_commentary_api(file_name):
    """Get commentary for top contributors"""
    try:
        data = request.json
        top_contributors = data.get('top_contributors')
        
        commentary = get_commentary(top_contributors, file_name)
        return jsonify({'commentary': commentary})
    except Exception as e:
        logger.error(f"Error getting commentary: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/modify-commentary/<file_name>', methods=['POST'])
def modify_commentary_api(file_name):
    """Modify commentary based on user input"""
    try:
        data = request.json
        user_comment = data.get('user_comment')
        current_commentary = data.get('current_commentary')
        selected_cells = data.get('selected_cells')
        contributing_columns = data.get('contributing_columns')
        top_n = data.get('top_n')
        
        updated_commentary = modify_commentary(
            user_comment,
            current_commentary,
            selected_cells,
            file_name,
            contributing_columns,
            top_n
        )
        
        return jsonify({'commentary': updated_commentary})
    except Exception as e:
        logger.error(f"Error modifying commentary: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chatbot', methods=['POST'])
def chatbot_api():
    """Process chatbot query"""
    try:
        data = request.json
        query = data.get('query')
        table_name = data.get('table_name')
        
        engine = get_engine()
        
        response = process_chatbot_query(engine, query, table_name)
        return jsonify({'response': response})
    except Exception as e:
        logger.error(f"Error processing chatbot query: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/update-config', methods=['POST'])
def update_config_api():
    """Update configuration for a file"""
    try:
        data = request.json
        file_name = data.get('file_name')
        contributing_columns = data.get('contributing_columns')
        top_n = data.get('top_n')
        
        # Read current config
        with open(CONFIG_FILE, 'r') as file:
            current_config = yaml.safe_load(file)
        
        # Update config
        current_config['excel_files'][file_name]['contributing_columns'] = contributing_columns
        current_config['excel_files'][file_name]['top_n'] = top_n
        
        # Write updated config
        with open(CONFIG_FILE, 'w') as file:
            yaml.dump(current_config, file)
        
        # Clear the cache to reload the updated config
        get_cached_file_config.cache_clear()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error updating config: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(e)}")
    return jsonify({'error': 'An unexpected error occurred. Please try again later.'}), 500

if __name__ == '__main__':
    # Use gunicorn for production
    app.run(debug=False, host='0.0.0.0', port=5000)