import asyncio
from app.database import engine, Base
from app.models import *

async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tablolar başarıyla oluşturuldu!")

if __name__ == "__main__":
    asyncio.run(init())