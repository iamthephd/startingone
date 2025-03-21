import io
from flask import Blueprint, jsonify, request, send_file
from backend.database.get_summary_table import get_summary_table
from backend.database.database_process import create_oracle_engine
from backend.database.get_top_contributors import get_top_attributes_by_difference
from backend.llm.reson_code import get_reason_code
from backend.llm.commentary import get_commentary, modify_commentary
from backend.llm.chatbot import process_chatbot_query
from backend.utils.helper import read_config, get_file_config_by_path
from backend.utils.ppt_export import generate_ppt

api_bp = Blueprint('api', __name__)

# Initialize database engine
config = read_config("config/config.yaml")
engine = create_oracle_engine(config.get('database', {}))

@api_bp.route('/summary-table/<file_name>', methods=['GET'])
def get_summary_table_route(file_name):
    try:
        file_config = get_file_config_by_path(config, file_name)
        df = get_summary_table(engine)
        return jsonify({
            'data': df.to_dict('records'),
            'columns': list(df.columns)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/top-contributors', methods=['POST'])
def calculate_top_contributors():
    try:
        data = request.json
        top_contributors = get_top_attributes_by_difference(
            engine,
            data['selected_cells'],
            data['table_name'],
            data['contributing_columns'],
            data['top_n']
        )
        return jsonify({'contributors': top_contributors})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/generate-commentary', methods=['POST'])
def generate_initial_commentary():
    try:
        data = request.json
        top_contributors = data['top_contributors']
        file_name = data['file_name']
        commentary = get_commentary(top_contributors, file_name)
        return jsonify({'commentary': commentary})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/modify-commentary', methods=['POST'])
def modify_existing_commentary():
    try:
        data = request.json
        modified_commentary = modify_commentary(
            data['user_comment'],
            data['current_commentary'],
            data['selected_cells'],
            data['file_name'],
            data['contributing_columns'],
            data['top_n']
        )
        return jsonify({'commentary': modified_commentary})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/chatbot', methods=['POST'])
def process_chat():
    try:
        query = request.json['query']
        response = process_chatbot_query(engine, query)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/generate-ppt', methods=['POST'])
def create_ppt():
    try:
        data = request.json
        ppt_buffer = generate_ppt(
            data['commentary'],
            data['selected_cells'],
            data['file_name']
        )

        # Convert PPT to bytes and send as file
        ppt_io = io.BytesIO(ppt_buffer.getvalue())
        return send_file(
            ppt_io,
            mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
            as_attachment=True,
            download_name=f"{data['file_name']}_presentation.pptx"
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500