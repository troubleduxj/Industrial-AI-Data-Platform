import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

# 添加项目根目录到 pythonpath
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import initialize_database
from app.models.device import DeviceInfo
from app.controllers.device_data import DeviceDataController
from tortoise import Tortoise

async def inspect_device_7621_utc():
    await initialize_database()
    
    device_id = 7621
    device = await DeviceInfo.filter(id=device_id).first()
    if not device:
        print("Device not found!")
        return

    controller = DeviceDataController()
    
    # 使用 UTC 时间查询
    # 模拟前端传来的 UTC 时间 (最近1小时)
    end_time_utc = datetime.now(timezone.utc)
    start_time_utc = end_time_utc - timedelta(hours=1)
    
    print(f"\nFetching history with UTC time: {start_time_utc} to {end_time_utc}")
    
    # 此时 start_time_utc 是 aware datetime
    # Controller 会直接 strftime，看看结果
    
    try:
        total, items = await controller.get_device_history_data(
            device_code=device.device_code,
            start_time=start_time_utc,
            end_time=end_time_utc,
            page=1,
            page_size=10
        )
        print(f"Total: {total}, Items: {len(items)}")
    except Exception as e:
        print(f"Error: {e}")

    await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(inspect_device_7621_utc())
