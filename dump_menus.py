
import asyncio
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from tortoise import Tortoise
from app.settings.config import settings
from app.models.admin import Menu

async def dump_menus():
    # Initialize Tortoise
    await Tortoise.init(config=settings.TORTOISE_ORM)
    
    menus = await Menu.all().order_by('parent_id', 'order_num')
    
    print(f"{'ID':<5} | {'Parent':<6} | {'Name':<30} | {'Path':<40} | {'Component':<40} | {'Icon'}")
    print("-" * 150)
    for m in menus:
        print(f"{m.id:<5} | {m.parent_id:<6} | {m.name:<30} | {m.path:<40} | {m.component:<40} | {m.icon}")

if __name__ == "__main__":
    asyncio.run(dump_menus())
