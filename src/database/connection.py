from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from src.core.config import settings

engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)