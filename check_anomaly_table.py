
import asyncio
from tortoise import Tortoise
from app.settings.config import settings
from app.models.ai_monitoring import AIAnomalyConfig

async def verify_anomaly_config_table():
    try:
        print("Initializing Tortoise ORM...")
        await Tortoise.init(config=settings.tortoise_orm.model_dump())
        print("Tortoise ORM initialized.")
        
        print("Checking connection...")
        conn = Tortoise.get_connection("default")
        await conn.execute_query("SELECT 1")
        print("Connection successful.")

        print("Checking if t_ai_anomaly_configs table exists...")
        # This query is specific to PostgreSQL
        result = await conn.execute_query(
            "SELECT to_regclass('public.t_ai_anomaly_configs')"
        )
        # result format for execute_query in asyncpg usually (affected_rows, rows)
        # rows is a list of Record objects
        
        print(f"Table check result: {result}")
        
        exists = False
        if result[1] and len(result[1]) > 0:
            val = result[1][0].get('to_regclass')
            if val:
                exists = True
        
        if exists:
            print("Table t_ai_anomaly_configs exists.")
        else:
            print("Table t_ai_anomaly_configs DOES NOT exist!")

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(verify_anomaly_config_table())
