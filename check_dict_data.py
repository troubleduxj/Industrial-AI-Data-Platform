import asyncio
import sys
from app.core.database import initialize_database, close_database
from app.models.system import SysDictType, SysDictData
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stdout, level="INFO")

async def main():
    await initialize_database()
    try:
        # List all dict types to find "监测字段分组"
        types = await SysDictType.all()
        target_type = None
        for t in types:
            if "分组" in t.type_name or "field" in t.type_code:
                logger.info(f"Found DictType: {t.type_name} ({t.type_code})")
                if "监测字段分组" in t.type_name or "device_field_group" in t.type_code:
                    target_type = t
        
        if target_type:
            logger.info(f"Checking data for {target_type.type_name} ({target_type.type_code})...")
            data_list = await SysDictData.filter(dict_type_id=target_type.id).all()
            for data in data_list:
                logger.info(f"  DictData: {data.data_label} ({data.data_value})")
                
            # Check if 'power' is in the values
            values = [d.data_value for d in data_list]
            if 'power' in values:
                logger.info("  'power' IS present in the dictionary.")
            else:
                logger.info("  'power' IS NOT present in the dictionary.")
        else:
            logger.info("Could not find a dictionary type matching '监测字段分组'.")

    finally:
        await close_database()

if __name__ == "__main__":
    asyncio.run(main())
