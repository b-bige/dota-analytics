from abc import ABC, abstractmethod

class BaseDotaClient(ABC):
    """
    Interface for any Dota 2 API provider.
    """
    @abstractmethod
    def request(self, **kwargs):
        """Makes a request to the API, checks for status and returns the raw data"""
        pass

    @abstractmethod 
    def get_match(self, match_id: int, **kwargs) -> dict:
        """
        Fetch a single match and return a standardized dictionary in the form of: \n
        {table_name: table_data}
        """
        pass

    @abstractmethod 
    def is_parsed_match(self, **kwargs) -> bool:
        """
        Fetch a single match and return a boolean indicating 
        whether the details of the match has been parsed yet.
        """
        pass