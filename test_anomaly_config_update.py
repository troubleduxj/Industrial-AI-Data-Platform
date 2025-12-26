
import asyncio
from tortoise import Tortoise
from app.settings.config import settings
from app.models.ai_monitoring import AIAnomalyConfig

async def test_update_config():
    try:
        print("Initializing Tortoise ORM...")
        await Tortoise.init(config=settings.tortoise_orm.model_dump())
        print("Tortoise ORM initialized.")
        
        device_code = "44258342-0eae-4653-981d-b51a5973db3a"
        config_data = {
            "thresholds": {
                "temperature": {"min": 20, "max": 80, "enabled": True},
                "pressure": {"min": 0.5, "max": 2.0, "enabled": True}
            },
            "mode": "rule"
        }
        username = "admin"
        
        print(f"Testing update for device {device_code}...")
        
        config = await AIAnomalyConfig.get_or_none(device_code=device_code)
        
        if config:
            print("Config found, updating...")
            config.config_data = config_data
            config.is_active = True
            config.updated_by = username
            await config.save()
            print("Update successful.")
        else:
            print("Config not found, creating...")
            config = await AIAnomalyConfig.create(
                device_code=device_code,
                config_data=config_data,
                is_active=True,
                updated_by=username
            )
            print("Creation successful.")
            
        print("Final config:", config.config_data)

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(test_update_config())
