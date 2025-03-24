import os
import yaml
import logging
import pandas as pd
from flask import Flask, render_template, request, jsonify, session
from pathlib import Path

from backend import read_config, get_file_config_by_path, convert_to_int, create_oracle_engine, get_details, get_top_attributes_by_difference, get_reason_code, get_commentary, modify_commentary, process_chatbot_query

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

data_path = "data"
config_file = "config/config.yaml"
excel_data_dir = "data"
config = read_config(config_file)


def load_engine(config):
    db_config = config['database']
    engine = create_oracle_engine(db_config)
    return engine

# loading the engine
engine = load_engine(config)

def save_config(updated_config):
    with open(config_file, "w") as file:
        yaml.dump(updated_config, file)


def update_commentary(selected_cells, contributing_columns, top_n):
    """Update commentary based on manual settings"""
    # This would be implemented elsewhere
    logger.debug(f"Updating commentary with {len(selected_cells)} cells, {len(contributing_columns)} columns, top {top_n}")
    # Get top attributes and generate commentary
    top_attrs = get_top_attributes_by_difference(engine, selected_cells, session["table"], contributing_columns, top_n)
    return get_commentary(top_attrs, session["table"])


@app.route('/')
def index():
    """Main application page"""
    return render_template('index.html')

@app.route('/api/files')
def get_files():
    """Get list of available files"""
    # This would typically come from a database or filesystem
    excel_file = [f for f in os.listdir(data_path)]
    file_list = [Path(f).stem for f in excel_file]
    
    return jsonify(file_list)

@app.route('/api/file_details', methods=['POST'])
def file_details():
    """Get details for a specific file"""
    data = request.json
    filename = data.get('filename')

    session['config_file'] = get_file_config_by_path(config, filename)
    session['table_name'] = session['config_file']['table_name']
    
    if not filename:
        return jsonify({"error": "No filename provided"}), 400
    
    try:
        # Get file details
        details = get_details(engine, session['table_name'])
        
        # Get summary table
        summary_func_name = session["file_config"].get('summary_table_function')
        summary_func = globals()[summary_func_name]
        df = summary_func(engine)
        df = df.map(convert_to_int)
        df = df.drop(columns=['Y/Y %', 'Q/Q %'])
        df = df.reset_index()

        # Convert DataFrame to dict for JSON serialization
        table_data = df.to_dict(orient='records')
        columns = df.columns.tolist()

        # Get selected cells
        selected_cells = get_reason_code(df.set_index(columns[0]), session["table_name"])
        
        # Get default values for this file from config
        file_config = config.get(filename, {})
        contributing_columns = file_config.get('contributing_columns', [])
        top_n = file_config.get('top_n', 3)
        
        # Get top attributes
        top_attrs = get_top_attributes_by_difference(engine, selected_cells, session["table_name"], contributing_columns, top_n)
        
        # Generate commentary
        commentary = get_commentary(top_attrs, session["table_name"])
        
        # Store in session for later use
        session['current_file'] = filename
        session['summary_table'] = table_data
        session['selected_cells'] = selected_cells
        session['contributing_columns'] = contributing_columns
        session['top_n'] = top_n
        session['commentary'] = commentary
        
        return jsonify({
            "details": details,
            "table": {
                "data": table_data,
                "columns": columns
            },
            "selected_cells": selected_cells,
            "contributing_columns": contributing_columns,
            "top_n": top_n,
            "commentary": commentary
        })
    
    except Exception as e:
        logger.error(f"Error processing file {filename}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/modify_commentary', methods=['POST'])
def api_modify_commentary():
    """Modify commentary based on user input"""
    data = request.json
    user_query = data.get('query')
    current_commentary = session.get('commentary', '')
    
    if not user_query:
        return jsonify({"error": "No query provided"}), 400
    
    try:
        # Call modify_commentary function
        updated_commentary = modify_commentary(user_query, current_commentary)
        
        # Update session
        session['commentary'] = updated_commentary
        
        return jsonify({"commentary": updated_commentary})
    
    except Exception as e:
        logger.error(f"Error modifying commentary: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/update_commentary', methods=['POST'])
def api_update_commentary():
    """Update commentary based on manual settings"""
    data = request.json
    selected_cells = data.get('selected_cells', [])
    contributing_columns = data.get('contributing_columns', [])
    top_n = data.get('top_n', 3)
    
    try:
        # Call update_commentary function
        updated_commentary = update_commentary(selected_cells, contributing_columns, top_n)
        
        # Update session
        session['selected_cells'] = selected_cells
        session['contributing_columns'] = contributing_columns
        session['top_n'] = top_n
        session['commentary'] = updated_commentary
        
        return jsonify({"commentary": updated_commentary})
    
    except Exception as e:
        logger.error(f"Error updating commentary: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/save_settings', methods=['POST'])
def api_save_settings():
    """Save settings to config file"""
    data = request.json
    filename = session.get('current_file')
    contributing_columns = data.get('contributing_columns', [])
    top_n = data.get('top_n', 3)
    
    if not filename:
        return jsonify({"error": "No file selected"}), 400
    
    try:
        # Update config
        global config
        current_config = read_config(config_file)
        current_config[filename]['contributing_columns'] = contributing_columns
        current_config[filename]['top_n'] = top_n

        # Save config
        if save_config(current_config):
            # Reload config
            config = current_config
            return jsonify({"success": True, "message": "Settings saved successfully"})
        else:
            return jsonify({"error": "Failed to save settings"}), 500
    
    except Exception as e:
        logger.error(f"Error saving settings: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chatbot', methods=['POST'])
def api_chatbot():
    """Handle chatbot interactions"""
    data = request.json
    query = data.get('query')
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    try:
        # Get chatbot reply
        reply = process_chatbot_query(engine, query, session['table_name'])
        
        return jsonify({"reply": reply})
    
    except Exception as e:
        logger.error(f"Error getting chatbot reply: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
