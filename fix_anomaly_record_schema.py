
import asyncio
from tortoise import Tortoise
from app.settings.config import settings

async def fix_anomaly_record_schema():
    try:
        await Tortoise.init(config=settings.tortoise_orm.model_dump())
        conn = Tortoise.get_connection("default")
        
        print("Altering t_ai_anomaly_records...")
        
        # 修改 detection_time 字段
        await conn.execute_query("ALTER TABLE t_ai_anomaly_records ALTER COLUMN detection_time TYPE timestamptz USING detection_time AT TIME ZONE 'Asia/Shanghai'")
        
        # 修改 created_at 字段
        await conn.execute_query("ALTER TABLE t_ai_anomaly_records ALTER COLUMN created_at TYPE timestamptz USING created_at AT TIME ZONE 'Asia/Shanghai'")
        
        # 修改 handle_time 字段 (如果是 nullable，也要处理)
        await conn.execute_query("ALTER TABLE t_ai_anomaly_records ALTER COLUMN handle_time TYPE timestamptz USING handle_time AT TIME ZONE 'Asia/Shanghai'")

        print("Schema updated for t_ai_anomaly_records.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(fix_anomaly_record_schema())
