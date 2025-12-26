import asyncio
import os
import sys
from tortoise import Tortoise

# Add project root to path
sys.path.append(os.getcwd())

from app.settings.config import settings

async def create_table():
    print("Initializing Tortoise...")
    await Tortoise.init(config=settings.tortoise_orm.model_dump())
    
    conn = Tortoise.get_connection("default")
    
    print("Creating table t_ai_anomaly_configs...")
    
    # Check if table exists
    check_sql = "SELECT to_regclass('public.t_ai_anomaly_configs')"
    res = await conn.execute_query(check_sql)
    if res and res[1] and res[1][0]['to_regclass']:
        print("Table already exists.")
        return

    # Create table
    # Using BIGSERIAL for id because BaseModel uses BigIntField
    sql = """
    CREATE TABLE IF NOT EXISTS "t_ai_anomaly_configs" (
        "id" BIGSERIAL NOT NULL PRIMARY KEY,
        "device_code" VARCHAR(50) NOT NULL UNIQUE,
        "config_data" JSONB NOT NULL DEFAULT '{}',
        "is_active" BOOLEAN NOT NULL DEFAULT TRUE,
        "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        "updated_by" VARCHAR(100)
    );
    """
    await conn.execute_query(sql)
    
    # Create Index
    index_sql = 'CREATE INDEX IF NOT EXISTS "idx_t_ai_anomal_device__code" ON "t_ai_anomaly_configs" ("device_code");'
    await conn.execute_query(index_sql)
    
    print("Table created successfully.")
    
    await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(create_table())
