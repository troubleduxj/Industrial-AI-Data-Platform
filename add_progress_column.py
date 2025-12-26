import asyncio
from tortoise import Tortoise
from app.settings.config import settings

async def add_progress_column():
    try:
        await Tortoise.init(config=settings.TORTOISE_ORM)
        conn = Tortoise.get_connection("default")
        
        print("Adding progress column to t_ai_models...")
        # Check if column exists first to avoid error if run multiple times
        try:
            await conn.execute_query('ALTER TABLE "t_ai_models" ADD COLUMN "progress" DOUBLE PRECISION DEFAULT 0.0;')
            print("Column 'progress' added successfully.")
        except Exception as e:
            if "already exists" in str(e):
                print("Column 'progress' already exists.")
            else:
                raise e
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(add_progress_column())
