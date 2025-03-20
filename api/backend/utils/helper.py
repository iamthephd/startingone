import yaml

def read_config(config_path):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def get_file_config_by_path(config, file_path):
    return config['excel_files'].get(file_path, {})
