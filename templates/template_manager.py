import yaml
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)

class TemplateManager:
    def __init__(self):
        self.summary_templates = self._load_templates('summary_template.yaml')
        self.insight_templates = self._load_templates('insight_template.yaml')
    
    def get_summary_template(self, table_name):
        """Get summary template for table"""
        try:
            return self.summary_templates[table_name]['prompt']
        except KeyError:
            logger.error(f"No summary template found for table {table_name}")
            raise ValueError(f"No summary template found for table {table_name}")
    
    def get_insight_template(self, table_name):
        """Get insight template for table"""
        try:
            return self.insight_templates[table_name]['prompt']
        except KeyError:
            logger.error(f"No insight template found for table {table_name}")
            raise ValueError(f"No insight template found for table {table_name}")
    
    def _load_templates(self, filename):
        """Load templates from YAML file"""
        try:
            template_path = Path(f"templates/llm/{filename}")
            with open(template_path) as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading templates from {filename}: {str(e)}")
            raise