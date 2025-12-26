
import asyncio
import os
import sys
from tortoise import Tortoise

# Add project root to python path
sys.path.append(os.getcwd())

from app.core.database import initialize_database

async def main():
    print("Initializing database...")
    await initialize_database()
    
    conn = Tortoise.get_connection("default")
    
    print("Checking mock data for /api/v2/devices/realtime/monitoring...")
    result = await conn.execute_query(
        "SELECT response_data FROM t_mock_data WHERE request_path = '/api/v2/devices/realtime/monitoring'"
    )
    
    if result and result[1]:
        print(f"Found {len(result[1])} rules.")
        for row in result[1]:
            print(f"Response Data: {row['response_data']}")
    else:
        print("No mock rule found.")

if __name__ == "__main__":
    asyncio.run(main())
