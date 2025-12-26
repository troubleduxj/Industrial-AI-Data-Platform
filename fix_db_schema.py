
import asyncio
from tortoise import Tortoise
from app.settings.config import settings

async def fix_schema():
    try:
        await Tortoise.init(config=settings.tortoise_orm.model_dump())
        conn = Tortoise.get_connection("default")
        
        print("Altering t_ai_anomaly_configs...")
        # Check if updated_at exists, if not create it (AIAnomalyConfig might not have had it if it was created raw?)
        # But verify_anomaly_config_table said table exists.
        
        # We need to handle the case where columns might already be timestamptz (unlikely given the error)
        
        await conn.execute_query("ALTER TABLE t_ai_anomaly_configs ALTER COLUMN created_at TYPE timestamptz USING created_at AT TIME ZONE 'Asia/Shanghai'")
        await conn.execute_query("ALTER TABLE t_ai_anomaly_configs ALTER COLUMN updated_at TYPE timestamptz USING updated_at AT TIME ZONE 'Asia/Shanghai'")
        
        print("Schema updated.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(fix_schema())
