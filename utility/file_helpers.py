from pathlib import Path
import yaml

def file_exists(file_name: str) -> bool:

    path = Path(file_name)

    return path.is_file()


def file_read_yaml(file_name: str) -> dict:

    with open(file_name, 'r') as stream:
        data = yaml.safe_load(stream)

    return data
