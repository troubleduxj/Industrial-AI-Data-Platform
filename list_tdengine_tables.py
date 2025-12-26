import asyncio
from app.core.tdengine_connector import TDengineConnector
from app.settings.config import TDengineCredentials

async def list_tables():
    creds = TDengineCredentials()
    connector = TDengineConnector(
        host=creds.host,
        port=creds.port,
        user=creds.user,
        password=creds.password,
        database=creds.database
    )
    
    print(f"Listing tables in {creds.database}...")
    try:
        res = await connector.query_data("SHOW TABLES")
        if res and 'data' in res:
            print(f"Found {len(res['data'])} tables.")
            for row in res['data'][:20]: # Print first 20
                print(row)
        else:
            print("No tables found.")
            
    except Exception as e:
        print(f"Error: {e}")

    await connector.close()

if __name__ == "__main__":
    asyncio.run(list_tables())
