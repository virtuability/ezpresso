
from typing import List, Dict

class PermissionSets:

    __permission_sets = None

    def __init__(self, permission_sets: dict):
        self.__permission_sets = permission_sets

    def get_stages(self) -> List[Dict]:
        return self.__permission_sets['stages']
