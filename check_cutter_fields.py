import asyncio
import os
import sys
from tortoise import Tortoise

# Add project root to path
sys.path.append(os.getcwd())

from app.settings.config import settings
from app.models.device import DeviceField

async def run():
    print("Initializing Tortoise...")
    await Tortoise.init(config=settings.TORTOISE_ORM)
    
    try:
        # Check fields for 'Cutter'
        fields = await DeviceField.filter(device_type_code="Cutter").all()
        print(f"Found {len(fields)} fields for 'Cutter'.")
        
        for field in fields:
            print(f"Field: {field.field_code}, Name: {field.field_name}, Monitor: {field.is_monitoring_key}, AI: {field.is_ai_feature}, Active: {field.is_active}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(run())
