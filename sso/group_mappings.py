class GroupMappings:
    def __init__(self, prefix: str, group_mappings: dict):

        self._group_mappings = group_mappings
        self._prefix = prefix

    @property
    def group_mappings(self):
        return self._group_mappings["sso_group_mappings"]

    @property
    def prefix(self):
        return self._prefix

    def get_mapping_by_name(self, group_name) -> dict:
        return next(
            item
            for item in self._group_mappings["sso_group_mappings"]
            if item["group_name"] == self._prefix + group_name
        )
