import asyncio
from app.core.tdengine_connector import TDengineConnector
from app.settings.config import TDengineCredentials

async def check_device_codes():
    creds = TDengineCredentials()
    connector = TDengineConnector(
        host=creds.host,
        port=creds.port,
        user=creds.user,
        password=creds.password,
        database=creds.database
    )
    
    print(f"Connecting to {creds.host}:{creds.port} db={creds.database}")
    
    # Check distinct device codes in Welding super table
    print("\n--- Distinct Device Codes in `Welding` ---")
    try:
        # Note: TDEngine might not support DISTINCT on tags in older versions, but let's try
        # Or just SELECT device_code FROM Welding LIMIT 10
        sql = "SELECT distinct device_code FROM `Welding`"
        print(f"Executing: {sql}")
        res = await connector.query_data(sql)
        if res and 'data' in res:
            for row in res['data']:
                print(row)
        else:
            print("No data or error:", res)
            
    except Exception as e:
        print(f"Error querying distinct device_code: {e}")
        
    await connector.close()

if __name__ == "__main__":
    asyncio.run(check_device_codes())
