import requests
import pandas as pd
import json

class APIClient:
    """Client for communicating with the backend API"""
    
    def __init__(self, base_url):
        """Initialize the API client with the base URL of the API"""
        self.base_url = base_url.rstrip('/')
        
    def _handle_response(self, response):
        """Handle API response and error cases"""
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            raise
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")
            raise
        except json.JSONDecodeError:
            print("Error decoding JSON response")
            return response.text
    
    def get_available_files(self):
        """Get list of available files from the backend"""
        response = requests.get(f"{self.base_url}/api/files")
        data = self._handle_response(response)
        return data.get('files', [])
    
    def get_file_config(self, file_name):
        """Get configuration for a specific file"""
        response = requests.get(f"{self.base_url}/api/file-config/{file_name}")
        return self._handle_response(response)
    
    def get_summary_table(self, file_name):
        """Get summary table data for a file"""
        response = requests.get(f"{self.base_url}/api/summary-table/{file_name}")
        data = self._handle_response(response)
        # Convert JSON data to pandas DataFrame
        df = pd.DataFrame.from_dict(data['data'])
        if 'index' in data:
            df.index = data['index']
        return df
    
    def get_reason_code(self, file_name, df):
        """Get reason code for the file"""
        df_json = df.to_json(orient='split')
        response = requests.post(
            f"{self.base_url}/api/reason-code/{file_name}",
            json={'df': df_json}
        )
        data = self._handle_response(response)
        return data['selected_cells']
    
    def get_top_contributors(self, file_name, selected_cells, contributing_columns, top_n):
        """Get top contributors for the selected cells"""
        # Ensure selected_cells is not None and is iterable
        if selected_cells is None:
            selected_cells = []
            
        payload = {
            'selected_cells': selected_cells,
            'contributing_columns': contributing_columns,
            'top_n': top_n
        }
        response = requests.post(
            f"{self.base_url}/api/top-contributors/{file_name}",
            json=payload
        )
        data = self._handle_response(response)
        return data['contributors']
    
    def get_commentary(self, file_name, top_contributors_formatted):
        """Get commentary for the top contributors"""
        payload = {
            'top_contributors': top_contributors_formatted
        }
        response = requests.post(
            f"{self.base_url}/api/commentary/{file_name}",
            json=payload
        )
        data = self._handle_response(response)
        return data['commentary']
    
    def modify_commentary(self, file_name, user_comment, current_commentary, selected_cells, 
                         contributing_columns, top_n):
        """Modify commentary based on user input"""
        # Ensure all parameters are properly defined and not None
        if selected_cells is None:
            selected_cells = []
        if contributing_columns is None:
            contributing_columns = []
        if top_n is None:
            top_n = 5  # Default value
        if current_commentary is None:
            current_commentary = ""
            
        payload = {
            'user_comment': user_comment,
            'current_commentary': current_commentary,
            'selected_cells': selected_cells,
            'contributing_columns': contributing_columns,
            'top_n': top_n
        }
        response = requests.post(
            f"{self.base_url}/api/modify-commentary/{file_name}",
            json=payload
        )
        data = self._handle_response(response)
        return data['commentary']
    
    def process_chatbot_query(self, query, table_name):
        """Process a chatbot query"""
        payload = {
            'query': query,
            'table_name': table_name
        }
        response = requests.post(
            f"{self.base_url}/api/chatbot",
            json=payload
        )
        data = self._handle_response(response)
        return data['response']
    
    def update_config(self, file_name, contributing_columns, top_n):
        """Update the configuration for a file"""
        payload = {
            'file_name': file_name,
            'contributing_columns': contributing_columns,
            'top_n': top_n
        }
        response = requests.post(
            f"{self.base_url}/api/update-config",
            json=payload
        )
        return self._handle_response(response)