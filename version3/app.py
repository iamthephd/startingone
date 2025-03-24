import os
import json
import logging
import pandas as pd
from flask import Flask, render_template, request, jsonify, session

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

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
    """Extract details from file like rows, average amount, etc."""
    # This would be implemented elsewhere
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
    """Generate summary table based on file name"""
    # This would be implemented elsewhere
    logger.debug(f"Generating summary table for file: {filename}")
    # Return a sample DataFrame
    data = {
        "Category": ["Category A", "Category B", "Category C", "Category D", "Category E"],
        "Q1": [100, 150, 200, 120, 180],
        "Q2": [110, 140, 190, 130, 170],
        "Q3": [120, 160, 210, 140, 190],
        "Q4": [130, 170, 220, 150, 200]
    }
    return pd.DataFrame(data)

def get_reason_code(df, filename):
    """Select cells based on summary table"""
    # This would be implemented elsewhere
    logger.debug(f"Getting reason codes for file: {filename}")
    # Return sample selected cells
    return [("Category A", "Q1", 100), ("Category C", "Q3", 210), ("Category E", "Q4", 200)]

def get_top_attributes(engine, selected_cells, contributing_columns, top_n):
    """Get top attributes"""
    # This would be implemented elsewhere
    logger.debug(f"Getting top attributes with {len(selected_cells)} selected cells")
    # Return sample data
    return {
        ("Category A", "Q1", 100): {"Factor 1": 40, "Factor 2": 35, "Factor 3": 25},
        ("Category C", "Q3", 210): {"Factor 4": 70, "Factor 5": 80, "Factor 6": 60},
        ("Category E", "Q4", 200): {"Factor 7": 55, "Factor 8": 90, "Factor 9": 55}
    }

def get_commentary(top_contributors):
    """Generate commentary based on top contributors"""
    # This would be implemented elsewhere
    logger.debug(f"Generating commentary based on {len(top_contributors)} contributors")
    
    # Make sure our cell references are explicitly mentioned in a consistent format
    # for the hover highlighting to work properly
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
    """Modify commentary based on user query"""
    # This would be implemented elsewhere
    logger.debug(f"Modifying commentary based on query: {user_query}")
    # For demonstration, append user query to current commentary
    return current_commentary + f"\n\nUpdated based on query: {user_query}"

def update_commentary(selected_cells, contributing_columns, top_n):
    """Update commentary based on manual settings"""
    # This would be implemented elsewhere
    logger.debug(f"Updating commentary with {len(selected_cells)} cells, {len(contributing_columns)} columns, top {top_n}")
    # Get top attributes and generate commentary
    top_attrs = get_top_attributes(None, selected_cells, contributing_columns, top_n)
    return get_commentary(top_attrs)

def chat_bot_reply(query):
    """Generate chatbot reply"""
    # This would be implemented elsewhere
    logger.debug(f"Generating chatbot reply for: {query}")
    return f"I understand you're asking about '{query}'. This is a system for analyzing financial data. How can I help you understand the current analysis?"

@app.route('/')
def index():
    """Main application page"""
    return render_template('index.html')

@app.route('/api/files')
def get_files():
    """Get list of available files"""
    # This would typically come from a database or filesystem
    files = ["financial_data_2023.csv", "revenue_report_q2.csv", "expense_analysis.csv"]
    return jsonify(files)

@app.route('/api/file_details', methods=['POST'])
def file_details():
    """Get details for a specific file"""
    data = request.json
    filename = data.get('filename')
    
    if not filename:
        return jsonify({"error": "No filename provided"}), 400
    
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
        current_config = load_config()
        current_config[filename] = {
            'contributing_columns': contributing_columns,
            'top_n': top_n
        }
        
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
        reply = chat_bot_reply(query)
        
        return jsonify({"reply": reply})
    
    except Exception as e:
        logger.error(f"Error getting chatbot reply: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
