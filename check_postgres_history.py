import asyncio
from tortoise import Tortoise
from app import settings
from app.models.device import DeviceHistoryData

async def check_postgres_history():
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgres://", 1)
    
    await Tortoise.init(
        db_url=db_url,
        modules={'models': ['app.models']}
    )
    
    count = await DeviceHistoryData.filter(device_id=7621).count()
    print(f"Postgres DeviceHistoryData count for device 7621: {count}")
    
    if count > 0:
        latest = await DeviceHistoryData.filter(device_id=7621).order_by('-created_at').first()
        print(f"Latest record: {latest.created_at}")

    await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(check_postgres_history())
