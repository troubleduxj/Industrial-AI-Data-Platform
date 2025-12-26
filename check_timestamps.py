import asyncio
from app.core.tdengine_connector import TDengineConnector
from app.settings.config import TDengineCredentials

async def check_data_timestamps():
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
    
    print(f"\n--- Checking Timestamps in `welding_real_data` for {device_code} ---")
    try:
        # Get min and max timestamp
        sql = f"SELECT min(ts), max(ts) FROM `welding_real_data` WHERE device_code = '{device_code}'"
        res = await connector.query_data(sql)
        if res and 'data' in res:
            print(f"Min TS: {res['data'][0][0]}")
            print(f"Max TS: {res['data'][0][1]}")
        else:
            print("No data or error:", res)
            
        # Get latest 5 records
        sql = f"SELECT ts FROM `welding_real_data` WHERE device_code = '{device_code}' ORDER BY ts DESC LIMIT 5"
        res = await connector.query_data(sql)
        if res and 'data' in res:
            print("Latest 5 timestamps:")
            for row in res['data']:
                print(row[0])
                
    except Exception as e:
        print(f"Error: {e}")

    await connector.close()

if __name__ == "__main__":
    asyncio.run(check_data_timestamps())
