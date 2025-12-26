import asyncio
import sys
import os
from tortoise import Tortoise

# Add project root to path
sys.path.append(os.getcwd())

from app.settings.config import settings
from app.models.system import SysDictType, SysDictData
from app.models.device import DeviceType

async def init_db():
    # Construct DB URL from .env.dev values manually for debugging
    db_url = "postgres://postgres:Hanatech@123@127.0.0.1:5432/devicemonitor"
    
    await Tortoise.init(
        db_url=db_url,
        modules={'models': ['app.models.system', 'app.models.device']}
    )

async def main():
    try:
        await init_db()
        
        print("\n=== Checking SysDictType ===")
        dict_types = await SysDictType.all()
        for dt in dict_types:
            print(f"ID: {dt.id}, Name: {dt.type_name}, Code: {dt.type_code}")
            
        print("\n=== Checking SysDictData (Sample) ===")
        # Check if there is any 'device_class' or similar
        potential_codes = ['device_type', 'device_class', 'equipment_type', 'equipment_class', 'device_category']
        for code in potential_codes:
            dt = await SysDictType.filter(type_code__icontains=code).first()
            if dt:
                print(f"\nFound DictType matching '{code}': {dt.type_name} ({dt.type_code})")
                data_items = await SysDictData.filter(dict_type_id=dt.id).all()
                for item in data_items:
                    print(f"  - Label: {item.data_label}, Value: {item.data_value}")
        
        print("\n=== Checking DeviceType Table ===")
        device_types = await DeviceType.all()
        for dt in device_types:
            print(f"ID: {dt.id}, Name: {dt.type_name}, Code: {dt.type_code}, Stable: {dt.tdengine_stable_name}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(main())
