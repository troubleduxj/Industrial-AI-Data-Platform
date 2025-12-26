import asyncio
from app.core.tdengine_connector import TDengineConnector
from app.settings.config import TDengineCredentials

async def check_data_content():
    creds = TDengineCredentials()
    connector = TDengineConnector(
        host=creds.host,
        port=creds.port,
        user=creds.user,
        password=creds.password,
        database=creds.database
    )
    
    print(f"Connecting to {creds.host}:{creds.port} db={creds.database}")
    
    device_code = "14323A0041"
    
    # Check welding_real_data
    print(f"\n--- Checking `welding_real_data` for {device_code} ---")
    try:
        sql = f"SELECT count(*) FROM `welding_real_data` WHERE device_code = '{device_code}'"
        res = await connector.query_data(sql)
        if res and 'data' in res:
            print(f"Count: {res['data'][0][0]}")
        else:
            print("No data or error:", res)
    except Exception as e:
        print(f"Error: {e}")

    # Check Welding
    print(f"\n--- Checking `Welding` for {device_code} ---")
    try:
        # Note: Welding table might use 'device_code' tag or similar. 
        # Describe first to be sure of column name if needed, but I'll assume device_code based on previous logs
        # Actually previous logs for Welding showed:
        # ['device_code', 'NCHAR', 255, 'TAG', 'disabled', 'disabled', 'disabled']
        sql = f"SELECT count(*) FROM `Welding` WHERE device_code = '{device_code}'"
        res = await connector.query_data(sql)
        if res and 'data' in res:
            print(f"Count: {res['data'][0][0]}")
        else:
            print("No data or error:", res)
    except Exception as e:
        print(f"Error: {e}")

    # Check device_14323A0041 direct table (if it exists)
    # Previous check said it didn't exist, but user said it does.
    # Maybe case sensitivity? device_14323a0041 vs device_14323A0041
    # User said: "device_{device_code}"
    print(f"\n--- Checking `device_{device_code}` direct query ---")
    try:
        sql = f"SELECT count(*) FROM `device_{device_code}`"
        res = await connector.query_data(sql)
        if res and 'data' in res:
            print(f"Count: {res['data'][0][0]}")
        else:
            print("No data or error:", res)
    except Exception as e:
        print(f"Error: {e}")

    await connector.close()

if __name__ == "__main__":
    asyncio.run(check_data_content())
