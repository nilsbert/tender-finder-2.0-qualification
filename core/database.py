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
        logger.info(f"Initializing {self.schema} database with Liquibase...")
        if "sqlite" in self.url:
            for table in QualificationBase.metadata.tables.values():
                table.schema = None

        import subprocess
        from urllib.parse import urlparse

        jdbc_url = self.url
        if "mssql+aioodbc" in self.url:
            parsed = urlparse(self.url)
            host = parsed.hostname
            port = parsed.port or 1433
            db_name = parsed.path.lstrip("/")
            user = parsed.username
            password = parsed.password
            jdbc_url = f"jdbc:sqlserver://{host}:{port};databaseName={db_name};user={user};password={password};encrypt=true;trustServerCertificate=true;"
        elif "sqlite" in self.url:
            path = self.url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
            jdbc_url = f"jdbc:sqlite:{path}"

        changelog_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "liquibase", "db.changelog-master.yaml")
        
        try:
            subprocess.run([
                "liquibase", 
                "--url", jdbc_url, 
                "--changeLogFile", changelog_path, 
                "update"
            ], check=True, capture_output=True, text=True)
            logger.info(f"{self.schema} database initialized successfully with Liquibase.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Liquibase failed: {e.stderr}")
            raise

    def get_session(self):
        return self.session_factory()

    async def get_all_keywords(self):
        from .models import Keyword
        from sqlalchemy import select
        async with self.session_factory() as session:
            result = await session.execute(select(Keyword))
            return result.scalars().all()

    async def get_categories(self):
        from sqlalchemy import text
        async with self.session_factory() as session:
            result = await session.execute(text("SELECT DISTINCT category FROM keywords WHERE category IS NOT NULL"))
            return [row[0] for row in result.all()]

    async def create_keyword(self, keyword_data):
        from .models import Keyword
        import uuid
        import datetime
        from sqlalchemy import select
        async with self.session_factory() as session:
            result = await session.execute(select(Keyword).where(Keyword.term == keyword_data.term))
            if result.scalars().first():
                raise DuplicateKeywordError(f"Keyword '{keyword_data.term}' already exists")
            kw_id = getattr(keyword_data, 'id', None) or str(uuid.uuid4())
            kw = Keyword(
                id=kw_id,
                term=keyword_data.term,
                weight=keyword_data.weight,
                type=keyword_data.type,
                sub_type=getattr(keyword_data, 'sub_type', None),
                sub_category=getattr(keyword_data, 'sub_category', None),
                category=getattr(keyword_data, 'category', None),
                created_at=datetime.datetime.now().isoformat()
            )
            session.add(kw)
            await session.commit()
            return kw

    async def update_keyword(self, keyword_id, keyword_data):
        from .models import Keyword
        from sqlalchemy import select
        async with self.session_factory() as session:
            result = await session.execute(select(Keyword).where(Keyword.id == keyword_id))
            kw = result.scalars().first()
            if not kw:
                return None
            if hasattr(keyword_data, 'term') and keyword_data.term is not None:
                kw.term = keyword_data.term
            if hasattr(keyword_data, 'weight') and keyword_data.weight is not None:
                kw.weight = keyword_data.weight
            if hasattr(keyword_data, 'type') and keyword_data.type is not None:
                kw.type = keyword_data.type
            if hasattr(keyword_data, 'sub_type') and keyword_data.sub_type is not None:
                kw.sub_type = keyword_data.sub_type
            if hasattr(keyword_data, 'sub_category') and keyword_data.sub_category is not None:
                kw.sub_category = keyword_data.sub_category
            if hasattr(keyword_data, 'category') and keyword_data.category is not None:
                kw.category = keyword_data.category
            await session.commit()
            return kw

    async def delete_keyword(self, keyword_id):
        from .models import Keyword
        from sqlalchemy import delete
        async with self.session_factory() as session:
            await session.execute(delete(Keyword).where(Keyword.id == keyword_id))
            await session.commit()

    async def get_tender_acl(self, tender_id):
        from .models import TenderACL
        from sqlalchemy import select
        async with self.session_factory() as session:
            result = await session.execute(select(TenderACL).where(TenderACL.id == tender_id))
            return result.scalars().first()

    async def get_score_distribution(self, search_text=None, website=None, keyword=None, rating_category=None):
        return {}



db = DatabaseManager("qualification")
