import asyncio
import sys
import os

# Add project root to python path
# migrate_alarms.py is in database/migrations/
# We need to go up 3 levels: migrations -> database -> DeviceMonitorV2
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import initialize_database, close_database
from app.models.device import WeldingAlarmHistory, DeviceAlarmHistory, DeviceInfo
from tortoise import Tortoise

async def migrate_alarms():
    print("Initializing database...")
    await initialize_database()
    
    try:
        # Get the actual connection to run raw SQL
        from tortoise import connections
        conn = connections.get("default")
        
        print("Applying schema changes to existing tables...")
        
        # 1. Add attributes to t_device_info
        await conn.execute_script('ALTER TABLE "t_device_info" ADD COLUMN IF NOT EXISTS "attributes" JSONB;')
        
        # 2. Add metrics to t_device_realtime_data
        await conn.execute_script('ALTER TABLE "t_device_realtime_data" ADD COLUMN IF NOT EXISTS "metrics" JSONB;')
        
        # Note: We are NOT dropping old columns (voltage, etc.) yet to preserve data 
        # until TDengine migration is fully verified or user explicitly requests cleanup.
        
        print("Creating table t_device_alarm_history...")
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS "t_device_alarm_history" (
            "id" BIGSERIAL NOT NULL PRIMARY KEY,
            "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
            "alarm_code" VARCHAR(50) NOT NULL,
            "severity" VARCHAR(20) NOT NULL  DEFAULT 'Error',
            "category" VARCHAR(50) NOT NULL  DEFAULT 'Device',
            "content" TEXT NOT NULL,
            "start_time" TIMESTAMPTZ NOT NULL,
            "end_time" TIMESTAMPTZ,
            "context" JSONB,
            "device_id" BIGINT NOT NULL REFERENCES "t_device_info" ("id") ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS "idx_t_device_al_device__232692" ON "t_device_alarm_history" ("device_id", "start_time");
        CREATE INDEX IF NOT EXISTS "idx_t_device_al_severit_3c6805" ON "t_device_alarm_history" ("severity");
        CREATE INDEX IF NOT EXISTS "idx_t_device_al_alarm_c_640688" ON "t_device_alarm_history" ("alarm_code");
        """
        await conn.execute_script(create_table_sql)
        
        # Skip global generate_schemas because it might fail on other unrelated tables
        # await Tortoise.generate_schemas(safe=True)
        
        print("Fetching old alarms...")
        try:
            old_alarms = await WeldingAlarmHistory.all()
        except Exception as e:
            print(f"Could not fetch old alarms (table might not exist or other error): {e}")
            return

        print(f"Found {len(old_alarms)} old alarm records.")
        
        count = 0
        skipped = 0
        
        for old_alarm in old_alarms:
            # Find mapping device
            device = await DeviceInfo.filter(device_code=old_alarm.prod_code).first()
            
            if not device:
                # print(f"Warning: Device not found for prod_code {old_alarm.prod_code}. Skipping.")
                skipped += 1
                continue
            
            # Check if already migrated
            exists = await DeviceAlarmHistory.filter(
                device=device,
                start_time=old_alarm.alarm_time,
                alarm_code=old_alarm.alarm_code
            ).exists()
            
            if exists:
                skipped += 1
                continue
                
            # Create new alarm
            await DeviceAlarmHistory.create(
                device=device,
                alarm_code=old_alarm.alarm_code,
                severity="Error", # Default
                category="Device", # Default
                content=old_alarm.alarm_message,
                start_time=old_alarm.alarm_time,
                end_time=old_alarm.alarm_end_time,
                context={
                    "solution": old_alarm.alarm_solution,
                    "duration_sec": old_alarm.alarm_duration_sec,
                    "original_prod_code": old_alarm.prod_code
                }
            )
            count += 1
            
            if count % 100 == 0:
                print(f"Migrated {count} records...")
                
        print(f"Migration completed.")
        print(f"Successfully migrated: {count}")
        print(f"Skipped (not found device or already exists): {skipped}")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Closing database...")
        await close_database()

if __name__ == "__main__":
    asyncio.run(migrate_alarms())
