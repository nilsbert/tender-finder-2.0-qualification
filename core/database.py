import os
import urllib.parse
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text, func
from datetime import datetime


class DuplicateKeywordError(Exception):
    pass


from .models import QualificationBase

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, schema_name):
        self.schema = schema_name
        conn_str = os.getenv("DATABASE_URL")
        if not conn_str or "sqlite" in conn_str:
            # Store in /data so a named Docker volume can persist across rebuilds
            os.makedirs("/data", exist_ok=True)
            self.url = f"sqlite+aiosqlite:////data/{schema_name}.db"
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
                await conn.execute(
                    text(
                        f"IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = '{self.schema}') EXEC('CREATE SCHEMA {self.schema}')"
                    )
                )
            await conn.run_sync(QualificationBase.metadata.create_all)
        logger.info(f"{self.schema} database initialized successfully.")

    def get_session(self):
        return self.session_factory()

    async def get_all_keywords(self):
        async with self.get_session() as session:
            from core.models import Keyword as ORMKeyword
            from sqlalchemy import select
            result = await session.execute(select(ORMKeyword))
            return result.scalars().all()

    async def get_categories(self):
        async with self.get_session() as session:
            from core.models import Keyword as ORMKeyword
            from sqlalchemy import select
            result = await session.execute(select(ORMKeyword.category).distinct())
            categories = [r for r in result.scalars().all() if r]
            if not categories:
                result = await session.execute(select(ORMKeyword.sub_type).distinct())
                categories = [r for r in result.scalars().all() if r]
            return categories

    async def create_keyword(self, keyword_in):
        async with self.get_session() as session:
            from core.models import Keyword as ORMKeyword
            from sqlalchemy import select, func
            import uuid
            from datetime import datetime, timezone
            
            stmt = select(ORMKeyword).where(func.lower(ORMKeyword.term) == keyword_in.term.lower())
            res = await session.execute(stmt)
            if res.scalars().first():
                raise DuplicateKeywordError(f"Keyword '{keyword_in.term}' already exists")
                
            db_kw = ORMKeyword(
                id=str(uuid.uuid4()),
                term=keyword_in.term,
                weight=keyword_in.weight,
                type=keyword_in.type,
                sub_type=keyword_in.sub_type,
                sub_category=keyword_in.sub_category,
                category=keyword_in.category,
                created_at=datetime.now(timezone.utc).isoformat()
            )
            session.add(db_kw)
            await session.commit()
            return db_kw

    async def update_keyword(self, keyword_id: str, keyword_input):
        async with self.get_session() as session:
            from core.models import Keyword as ORMKeyword
            from sqlalchemy import select
            
            stmt = select(ORMKeyword).where(ORMKeyword.id == keyword_id)
            result = await session.execute(stmt)
            db_kw = result.scalars().first()
            if not db_kw:
                return None
                
            db_kw.term = keyword_input.term
            db_kw.weight = keyword_input.weight
            db_kw.type = keyword_input.type
            db_kw.sub_type = keyword_input.sub_type
            db_kw.sub_category = keyword_input.sub_category
            db_kw.category = keyword_input.category
            
            await session.commit()
            return db_kw

    async def delete_keyword(self, keyword_id: str) -> bool:
        async with self.get_session() as session:
            from core.models import Keyword as ORMKeyword
            from sqlalchemy import select, delete
            
            stmt = select(ORMKeyword).where(ORMKeyword.id == keyword_id)
            result = await session.execute(stmt)
            db_kw = result.scalars().first()
            if not db_kw:
                return False
                
            await session.execute(delete(ORMKeyword).where(ORMKeyword.id == keyword_id))
            await session.commit()
            return True

    async def get_tender_acl(self, tender_id: str):
        async with self.get_session() as session:
            from core.models import TenderACL as ORMTender
            from sqlalchemy import select
            stmt = select(ORMTender).where(ORMTender.id == tender_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def upsert_tender_acl(self, data: dict):
        async with self.get_session() as session:
            from core.models import TenderACL as ORMTender
            from sqlalchemy import select
            
            tender_id = data.get("id")
            stmt = select(ORMTender).where(ORMTender.id == tender_id)
            result = await session.execute(stmt)
            db_tender = result.scalars().first()
            
            if not db_tender:
                db_tender = ORMTender(id=tender_id)
                session.add(db_tender)
                
            db_tender.title = data.get("title", db_tender.title)
            db_tender.description = data.get("description", db_tender.description)
            db_tender.full_text = data.get("full_text", db_tender.full_text)
            db_tender.score = data.get("score", db_tender.score)
            db_tender.status = data.get("status", db_tender.status)
            db_tender.source_system = data.get("source_system", db_tender.source_system)
            
            await session.commit()

    async def get_config(self, config_id: str) -> dict:
        async with self.get_session() as session:
            from core.models import ConfigORM
            from sqlalchemy import select
            stmt = select(ConfigORM).where(ConfigORM.key == config_id)
            result = await session.execute(stmt)
            cfg = result.scalars().first()
            return cfg.value if cfg else {}

    async def get_score_distribution(self, search_text=None, website=None, keyword=None, rating_category=None):
        async with self.get_session() as session:
            from core.models import TenderACL as ORMTender
            from sqlalchemy import select
            
            stmt = select(ORMTender.score)
            result = await session.execute(stmt)
            scores = result.scalars().all()
            
            distribution = {
                "0-1": 0,
                "1-3": 0,
                "3-5": 0,
                "5+": 0
            }
            for s in scores:
                if s < 1:
                    distribution["0-1"] += 1
                elif s < 3:
                    distribution["1-3"] += 1
                elif s < 5:
                    distribution["3-5"] += 1
                else:
                    distribution["5+"] += 1
            return distribution


db = DatabaseManager("qualification")

