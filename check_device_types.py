import asyncio
import os
import sys
from tortoise import Tortoise

# Add project root to path
sys.path.append(os.getcwd())

from app.settings.config import settings
from app.models.device import DeviceInfo

async def run():
    print("Initializing Tortoise...")
    await Tortoise.init(config=settings.TORTOISE_ORM)
    
    try:
        # Check distinct device types
        types = await DeviceInfo.all().distinct().values_list("device_type", flat=True)
        print(f"Available device types: {types}")
        
        # Check count for 'Cutter' (case insensitive search might be needed if exact match fails)
        cutter_count = await DeviceInfo.filter(device_type="Cutter").count()
        print(f"Devices with device_type='Cutter': {cutter_count}")
        
        if cutter_count == 0:
             # Try case insensitive
             cutter_count_ci = await DeviceInfo.filter(device_type__iexact="cutter").count()
             print(f"Devices with device_type (case-insensitive) 'cutter': {cutter_count_ci}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(run())
