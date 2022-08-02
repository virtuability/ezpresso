
class AccountStructure:

   __account_structure = None

   def __init__(self, account_structure: dict):
      self.__account_structure = account_structure

   def get_account_structure(self) -> dict:
      return self.__account_structure

   def get_accounts(self) -> dict:
      return self.__account_structure['Accounts']
