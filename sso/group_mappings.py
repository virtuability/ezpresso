
class GroupMappings:

   __group_mappings = None

   def __init__(self, prefix: str, group_mappings: dict):

      self.__group_mappings = group_mappings
      self.__prefix = prefix

   def get_group_mappings(self):
      return self.__group_mappings['group_mappings']

   def get_prefix(self):
      return self.__prefix

   def get_mapping_by_name(self, group_name) -> dict:
      return next(item for item in self.get_group_mappings() if item["group_name"] == self.__prefix + group_name)
