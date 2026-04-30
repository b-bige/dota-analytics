from abc import ABC, abstractmethod
from src.database import DatabaseManager
from datetime import datetime, timedelta
from src.dashboard.query_builder import QueryBuilder
import dash_mantine_components as dmc
from dash import html, no_update
from src.dashboard import db_manager

class Filter(ABC):
    db = db_manager
    filter_name: str
    component_id: str

    @staticmethod
    def handle_filters(qb: QueryBuilder, exclude=None, **kwargs):
        """Takes a QueryBuilder, and adds any applied filters to it."""
        from . import FILTER_MAP
        for filter_name, value in kwargs.items():
            if filter_name in FILTER_MAP:
                FILTER_MAP[filter_name].apply_to_query(
                    qb, value, exclude=(filter_name == exclude)
                )
        return qb

    @abstractmethod
    def parse_from_url(self, params: dict):
        """Parses the filters from the URL search to a dictionary."""
        return params.get(self.filter_name, None)
    
    @abstractmethod
    def apply_to_query(self, qb, value, exclude: bool):
        """Applies specific filter condition to QueryBuilder."""
        pass

    @abstractmethod
    def to_url_params(self, value) -> dict:
        """Makes the dictionary from the filter for URL search parsing.""" 
        return {self.filter_name: value} if value else {}

    @abstractmethod
    def get_data(self, **filters):
        """Fetch available options for this filter"""
        pass

    @abstractmethod
    def render(self, value, data, **kwargs):
        """Return the Mantine component for this filter"""
        pass

    def get_updated_data(self, triggered_component_id, **filters):
        """Return no_update if this filter triggered, otherwise fetch fresh data"""
        if triggered_component_id == self.component_id:
            return no_update
        return self.get_data(exclude=self.filter_name, **filters)

    def get_outputs(self, triggered_component_id, **filters) -> list:
        """Return list of output values for this filter — override for multi-output filters"""
        return [self.get_updated_data(triggered_component_id, **filters)]