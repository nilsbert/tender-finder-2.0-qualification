import os
import urllib.parse
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
class DuplicateKeywordError(Exception):
    pass

from .models import QualificationBase

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, schema_name):
        self.schema = schema_name
        conn_str = os.getenv("DATABASE_URL")
        if not conn_str or "sqlite" in conn_str:
            self.url = f"sqlite+aiosqlite:///{schema_name}.db"
        else:
            self.url = conn_str
        self.engine = create_async_engine(self.url, pool_pre_ping=True)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def init_db(self):
        logger.info(f"Initializing {self.schema} database...")
        if "sqlite" in self.url:
            for table in QualificationBase.metadata.tables.values():
                table.schema = None
        
        async with self.engine.begin() as conn:
            if "mssql" in self.url:
                await conn.execute(text(f"IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = '{self.schema}') EXEC('CREATE SCHEMA {self.schema}')"))
            await conn.run_sync(QualificationBase.metadata.create_all)
        logger.info(f"{self.schema} database initialized successfully.")

    def get_session(self):
        return self.session_factory()

db = DatabaseManager("qualification")
