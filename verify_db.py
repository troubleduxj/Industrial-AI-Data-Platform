import asyncio
from tortoise import Tortoise
from app.settings.config import settings
from app.models.ai_monitoring import AIModel

async def verify_db():
    try:
        print("Initializing Tortoise ORM...")
        await Tortoise.init(config=settings.tortoise_orm.model_dump())
        print("Tortoise ORM initialized.")
        
        print("Checking connection...")
        conn = Tortoise.get_connection("default")
        await conn.execute_query("SELECT 1")
        print("Connection successful.")

        print("Checking if t_ai_models table exists...")
        # This query is specific to PostgreSQL which seems to be the DB used (asyncpg)
        result = await conn.execute_query(
            "SELECT to_regclass('public.t_ai_models')"
        )
        print(f"Table check result: {result}")
        
        if result[1][0]['to_regclass']:
            print("Table t_ai_models exists.")
            print("Counting models...")
            count = await AIModel.all().count()
            print(f"Model count: {count}")
            
            # Try to fetch one to see if fields match
            model = await AIModel.first()
            if model:
                print(f"First model: {model.model_name}")
            else:
                print("No models found.")
        else:
            print("Table t_ai_models DOES NOT exist!")

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(verify_db())
