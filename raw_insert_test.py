
import asyncio
from tortoise import Tortoise
from app.settings.config import settings
from datetime import datetime, timezone

async def raw_insert():
    try:
        await Tortoise.init(config=settings.tortoise_orm.model_dump())
        conn = Tortoise.get_connection("default")
        
        now = datetime.now(timezone.utc)
        print(f"Inserting {now}")
        
        try:
            await conn.execute_query(
                "INSERT INTO t_ai_anomaly_configs (device_code, config_data, is_active, created_at, updated_at, updated_by) VALUES ($1, $2, $3, $4, $5, $6)",
                ["test_device_raw", "{}", True, now, now, "test"]
            )
            print("Success")
        except Exception as e:
            print(f"Failed: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"Init Failed: {e}")
    finally:
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(raw_insert())
