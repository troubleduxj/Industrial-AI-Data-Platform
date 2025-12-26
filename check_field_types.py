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
        # Check distinct device_type_code in DeviceField
        types = await DeviceField.all().distinct().values_list("device_type_code", flat=True)
        print(f"DeviceField type codes: {types}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(run())
