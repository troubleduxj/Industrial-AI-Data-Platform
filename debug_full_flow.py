
import asyncio
import logging
from datetime import datetime
from tortoise import Tortoise
from app.settings.config import settings
from app.services.data_query_service import data_query_service

# Configure logging
logging.basicConfig(level=logging.INFO)

async def main():
    try:
        db_url = settings.DATABASE_URL
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgres://", 1)
            
        await Tortoise.init(
            db_url=db_url,
            modules={"models": ["app.models.device", "app.models.admin"]}
        )
        
        print("\n--- Debug Full Query Flow ---")
        
        # Simulate frontend parameters
        model_code = "real_data_cutter"
        device_code = "0f3cf01c-0fec-4d3b-93ff-65443c691ab6" # Correct UUID
        # Time range from screenshot: 2025-12-02 00:00 -> 2025-12-03 00:00
        # Assuming frontend sends local time, FastAPI converts to datetime
        # Let's try naive datetime first (as received by FastAPI usually if no timezone info)
        start_time = datetime(2025, 12, 2, 0, 0, 0)
        end_time = datetime(2025, 12, 3, 0, 0, 0)
        
        print(f"Params: model={model_code}, device={device_code}")
        print(f"Time: {start_time} -> {end_time}")
        
        # Force close any existing connection
        if data_query_service.tdengine_connector:
            await data_query_service.tdengine_connector.close()
            data_query_service.tdengine_connector = None

        try:
            result = await data_query_service.query_realtime_data(
                model_code=model_code,
                device_code=device_code,
                start_time=start_time,
                end_time=end_time,
                page=1,
                page_size=50,
                log_execution=True
            )
            
            print("\n--- Query Result ---")
            print(f"Total: {result.get('total')}")
            print(f"Generated SQL: {result.get('generated_sql')}")
            
            data = result.get('data', [])
            print(f"Data Count: {len(data)}")
            if data:
                print(f"First Row Keys: {list(data[0].keys())}")
                print(f"First Row Sample: {data[0]}")
            else:
                print("DATA IS EMPTY!")
                
        except Exception as e:
            print(f"Query Failed: {e}")
            import traceback
            traceback.print_exc()

    except Exception as e:
        print(f"Setup Error: {e}")
    finally:
        await Tortoise.close_connections()
        if data_query_service.tdengine_connector:
             await data_query_service.tdengine_connector.close()

if __name__ == "__main__":
    asyncio.run(main())
