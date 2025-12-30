import asyncio
import sys
import os

# Add the backend/api directory to the path so we can import modules
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from api.common.database import engine
from api.common.models import Base, SystemSetting
from api.common.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

async def init_db():
    async with engine.begin() as conn:
        # Import all models here to ensure they are registered with Base.metadata
        await conn.run_sync(Base.metadata.create_all)
    
    # Seed settings
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        default_settings = {
            "GOOGLE_CLOUD_PROJECT": settings.GOOGLE_CLOUD_PROJECT,
            "GOOGLE_CLOUD_LOCATION": settings.GOOGLE_CLOUD_LOCATION,
            "AI_MODEL_NAME": settings.AI_MODEL_NAME,
            "GOOGLE_APPLICATION_CREDENTIALS": settings.GOOGLE_APPLICATION_CREDENTIALS
        }
        for key, value in default_settings.items():
            if value:
                from sqlalchemy import select
                result = await session.execute(select(SystemSetting).where(SystemSetting.key == key))
                if not result.scalar_one_or_none():
                    session.add(SystemSetting(key=key, value=value))
        await session.commit()
        
    print("Database initialized and settings seeded successfully.")

if __name__ == "__main__":
    asyncio.run(init_db())
