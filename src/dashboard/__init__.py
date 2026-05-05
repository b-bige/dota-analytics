from dash import Dash
from src.database import DatabaseManager
from src.core.logger import setup_logger

db_manager = DatabaseManager()
listener = setup_logger(logfile_path='logs/dashboard.log')
from src.dashboard.filters import Filter
Filter.db = db_manager

app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True)
server = app.server

__all__ = ["app", "db", "listener"]