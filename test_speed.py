
import asyncio
import time
import logging
from app.settings.config import TDengineCredentials
from app.core.tdengine_connector import TDengineConnector

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_connector_init_speed():
    print("Loading creds once...")
    start_time = time.time()
    creds = TDengineCredentials()
    print(f"Creds load time: {time.time() - start_time:.4f}s")
    
    print("Testing connector init speed...")
    start_time = time.time()
    connector = TDengineConnector(
        host=creds.host,
        port=creds.port,
        user=creds.user,
        password=creds.password,
        database=creds.database
    )
    print(f"Connector init time: {time.time() - start_time:.4f}s")
    
    await connector.close()

if __name__ == "__main__":
    asyncio.run(test_connector_init_speed())
