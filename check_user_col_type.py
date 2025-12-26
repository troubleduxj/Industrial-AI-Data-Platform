
import asyncio
from tortoise import Tortoise
from app.settings.config import settings

async def check_user_column_type():
    try:
        await Tortoise.init(config=settings.tortoise_orm.model_dump())
        conn = Tortoise.get_connection("default")
        res = await conn.execute_query(
            "SELECT data_type FROM information_schema.columns WHERE table_name = 't_sys_user' AND column_name = 'created_at'"
        )
        print(f"User created_at type: {res}")
    except Exception as e:
        print(e)
    finally:
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(check_user_column_type())
