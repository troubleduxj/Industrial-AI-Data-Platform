
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.core.tdengine_connector import TDengineConnector
from app.core.tdengine_config import tdengine_config_manager

async def main():
    try:
        # Initialize config
        tdengine_config_manager.set_default_server("main")
        
        connector = TDengineConnector()
        print(f"Connected to {connector.base_url}")
        
        # Try to describe a non-existent table
        table_name = "non_existent_table_12345"
        print(f"Describing table: {table_name}")
        
        sql = f"DESCRIBE {table_name}"
        result = await connector.execute_sql(sql)
        
        print("Result:", result)
        
        await connector.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
