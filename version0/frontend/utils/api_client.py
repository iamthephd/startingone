import requests
import logging

logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        logger.debug(f"Initializing API client with base URL: {self.base_url}")

    def _make_request(self, method, endpoint, **kwargs):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        logger.debug(f"Making {method} request to {url}")
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise

    def get_summary_table(self, file_name):
        try:
            response = self._make_request('GET', f"summary-table/{file_name}")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get summary table: {str(e)}")
            return {"error": str(e)}

    def get_top_contributors(self, selected_cells, table_name, contributing_cols, top_n):
        try:
            response = self._make_request(
                'POST',
                "top-contributors",
                json={
                    'selected_cells': selected_cells,
                    'table_name': table_name,
                    'contributing_columns': contributing_cols,
                    'top_n': top_n
                }
            )
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get top contributors: {str(e)}")
            return {"error": str(e)}

    def generate_commentary(self, top_contributors, file_name):
        try:
            response = self._make_request(
                'POST',
                "generate-commentary",
                json={
                    'top_contributors': top_contributors,
                    'file_name': file_name
                }
            )
            return response.json()
        except Exception as e:
            logger.error(f"Failed to generate commentary: {str(e)}")
            return {"error": str(e)}

    def modify_commentary(self, user_comment, current_commentary, selected_cells, 
                         file_name, contributing_cols, top_n):
        try:
            response = self._make_request(
                'POST',
                "modify-commentary",
                json={
                    'user_comment': user_comment,
                    'current_commentary': current_commentary,
                    'selected_cells': selected_cells,
                    'file_name': file_name,
                    'contributing_columns': contributing_cols,
                    'top_n': top_n
                }
            )
            return response.json()
        except Exception as e:
            logger.error(f"Failed to modify commentary: {str(e)}")
            return {"error": str(e)}

    def process_chat(self, query):
        try:
            response = self._make_request(
                'POST',
                "chatbot",
                json={'query': query}
            )
            return response.json()
        except Exception as e:
            logger.error(f"Failed to process chat: {str(e)}")
            return {"error": str(e)}

    def generate_ppt(self, commentary, selected_cells, file_name):
        try:
            response = self._make_request(
                'POST',
                "generate-ppt",
                json={
                    'commentary': commentary,
                    'selected_cells': selected_cells,
                    'file_name': file_name
                }
            )
            return response.content
        except Exception as e:
            logger.error(f"Failed to generate PPT: {str(e)}")
            raise