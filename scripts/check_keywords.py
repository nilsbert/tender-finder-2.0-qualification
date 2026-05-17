import asyncio
import os
import sys
from sqlalchemy import text

# Add parent directory to path to import qualification.core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database import db

async def check_keywords():
    try:
        await db.init_db()
        async with db.get_session() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM keywords"))
            count = result.scalar()
            print(f"KEYWORD_COUNT:{count}")
            
            if count == 0:
                print("No keywords found. I should probably upload initial data.")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(check_keywords())
