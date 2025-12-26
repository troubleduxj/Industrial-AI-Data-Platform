import asyncio
import os
import sys
from tortoise import Tortoise

# Add project root to path
sys.path.append(os.getcwd())

from app.core.tdengine_connector import TDengineConnector

async def check_tdengine():
    print("Checking TDengine connection...")
    
    try:
        host = os.getenv("TDENGINE_HOST", "192.168.237.170")
        database = "hlzg_db"
        print(f"Target Host: {host}, Database: {database}")
        
        connector = TDengineConnector(host=host, database=database)
        
        # Candidate table names
        device_code_uuid = "44258342-0eae-4653-981d-b51a5973db3a"
        candidates = [
            f"device_{device_code_uuid}", # With hyphens
            f"`device_{device_code_uuid}`", # With hyphens and backticks
            f"device_{device_code_uuid.replace('-', '_')}", # With underscores
        ]
        
        for table_name in candidates:
            print(f"\nTesting table: {table_name}")
            sql = f"SELECT last_row(*) FROM {table_name}"
            print(f"   Executing: {sql}")
            try:
                res = await connector.query_data(sql)
                print(f"   Result: {res}")
                if res and res.get('data'):
                    print("   ✅ Data found!")
                    # Print columns if available
                    if res.get('column_meta'):
                         print(f"   Columns: {[col[0] for col in res['column_meta']]}")
                    break
            except Exception as e:
                print(f"   ❌ Query failed: {e}")

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_tdengine())
