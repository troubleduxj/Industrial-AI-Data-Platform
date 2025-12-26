import asyncio
from tortoise import Tortoise
from app import settings
from app.models.device import DeviceInfo, DeviceType

async def check_device_info():
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgres://", 1)
    
    await Tortoise.init(
        db_url=db_url,
        modules={'models': ['app.models']}
    )
    
    device = await DeviceInfo.get_or_none(id=7621)
    if not device:
        print("Device 7621 not found")
        return

    print(f"Device ID: {device.id}")
    print(f"Device Name: {device.device_name}")
    print(f"Device Code: {device.device_code}")
    print(f"Device Type Code: {device.device_type}")
    
    if device.device_type:
        device_type = await DeviceType.get_or_none(type_code=device.device_type)
        if device_type:
            print(f"Device Type Name: {device_type.type_name}")
            print(f"TDengine Stable Name: {device_type.tdengine_stable_name}")
        else:
            print(f"Device Type {device.device_type} not found in DB")
    else:
        print("Device has no type")

    await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(check_device_info())
