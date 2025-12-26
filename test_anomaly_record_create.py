
import asyncio
from tortoise import Tortoise
from app.settings.config import settings
from app.models.ai_monitoring import AIAnomalyRecord
from datetime import datetime

async def test_create_record():
    try:
        print("Initializing Tortoise ORM...")
        await Tortoise.init(config=settings.tortoise_orm.model_dump())
        print("Tortoise ORM initialized.")
        
        device_code = "44258342-0eae-4653-981d-b51a5973db3a"
        
        print(f"Testing create record for device {device_code}...")
        
        await AIAnomalyRecord.create(
            device_code=device_code,
            device_name="Test Device",
            anomaly_type="combined",
            severity="低",
            anomaly_score=0.5,
            detection_time=datetime.now(),
            anomaly_data={
                "anomalies": [],
                "data_points": 5,
                "anomaly_rate": 0.0
            },
            is_handled=False
        )
        print("Record created successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(test_create_record())
