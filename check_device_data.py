import asyncio
import os
import sys
from tortoise import Tortoise
import datetime

# Add project root to python path
sys.path.append(os.getcwd())

from app.settings.config import settings
from app.models.device import DeviceInfo, DeviceRealTimeData

async def main():
    print("Initializing database...")
    # Initialize Tortoise
    await Tortoise.init(config=settings.tortoise_orm.model_dump())
    
    try:
        # 1. Find the device "Cutter01"
        print("Searching for device 'Cutter01'...")
        device = await DeviceInfo.get_or_none(device_name="Cutter01")
        
        if not device:
            print("Device 'Cutter01' not found by name. Trying device_code='Cutter01'...")
            device = await DeviceInfo.get_or_none(device_code="Cutter01")
            
        if not device:
            print("Device 'Cutter01' not found!")
            # List all devices to help debug
            devices = await DeviceInfo.all().limit(10)
            print("Available devices (first 10):")
            for d in devices:
                print(f" - {d.device_name} ({d.device_code})")
            return

        print(f"Found device: {device.device_name} (ID: {device.id}, Code: {device.device_code})")

        # 2. Check RealTimeData
        realtime_data = await DeviceRealTimeData.get_or_none(device=device)
        
        if realtime_data:
            print(f"Found existing real-time data for device {device.id}:")
            print(f" - Status: {realtime_data.status}")
            print(f" - Metrics: {realtime_data.metrics}")
            print(f" - Timestamp: {realtime_data.data_timestamp}")
            
            # Update with new data to trigger UI update
            print("Updating with fresh mock data...")
            realtime_data.metrics = {
                "cutting_speed": 120.5,
                "arc_voltage": 45.2,
                "gas_pressure": 0.8,
                "torch_height": 15.0,
                "cutting_current": 100.0
            }
            realtime_data.status = "online"
            realtime_data.data_timestamp = datetime.datetime.now()
            await realtime_data.save()
            print("Data updated.")
            
        else:
            print(f"No real-time data found for device {device.id}. Creating new record...")
            await DeviceRealTimeData.create(
                device=device,
                metrics={
                    "cutting_speed": 120.5,
                    "arc_voltage": 45.2,
                    "gas_pressure": 0.8,
                    "torch_height": 15.0,
                    "cutting_current": 100.0
                },
                status="online",
                data_timestamp=datetime.datetime.now()
            )
            print("New real-time data record created.")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(main())
