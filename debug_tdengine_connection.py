
import asyncio
import time
import logging
from app.settings.config import TDengineCredentials
from app.core.tdengine_connector import TDengineConnector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_connection():
    device_code = "44258342-0eae-4653-981d-b51a5973db3a"
    table_name = f"`device_{device_code}`"
    sql = f"SELECT last_row(*) FROM {table_name}"
    
    print(f"Testing query: {sql}")
    
    connector = None
    try:
        start_time = time.time()
        
        tdengine_creds = TDengineCredentials()
        connector = TDengineConnector(
            host=tdengine_creds.host,
            port=tdengine_creds.port,
            user=tdengine_creds.user,
            password=tdengine_creds.password,
            database=tdengine_creds.database
        )
        
        init_time = time.time()
        print(f"Connector init time: {init_time - start_time:.4f}s")
        
        res = await connector.query_data(sql)
        query_time = time.time()
        print(f"Query time: {query_time - init_time:.4f}s")
        print(f"Result code: {res.get('code')}")
        if res.get('data'):
            print(f"Data found: {res.get('data')}")
        else:
            print("No data found")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if connector:
            await connector.close()
            print("Connector closed")

if __name__ == "__main__":
    asyncio.run(test_connection())
