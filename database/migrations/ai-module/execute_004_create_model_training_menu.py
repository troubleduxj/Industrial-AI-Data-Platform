import asyncio
import sys
from pathlib import Path
from tortoise import Tortoise

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[3]))

from app.settings import settings

async def execute_migration():
    """Execute database migration for Model Training menu"""
    
    print("=" * 60)
    print("🚀 Starting AI Module Menu Migration (Model Training)")
    print("=" * 60)
    print()
    
    # Initialize DB connection
    try:
        db_url = settings.DATABASE_URL
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgres://", 1)
            
        await Tortoise.init(
            db_url=db_url,
            modules={'models': ['app.models']}
        )
        print("✅ Database connected successfully")
        print(f"   DB URL: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'N/A'}")
        print()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Read SQL file
    migration_file = Path(__file__).parent / "004_create_model_training_menu.sql"
    
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False
    
    print(f"📄 Reading migration file: {migration_file.name}")
    
    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        print(f"✅ Migration file read successfully ({len(sql_content)} chars)")
        print()
    except Exception as e:
        print(f"❌ Failed to read migration file: {e}")
        return False
    
    # Execute SQL
    print("🔄 Executing SQL migration...")
    print("-" * 60)
    
    conn = Tortoise.get_connection("default")
    
    try:
        await conn.execute_script(sql_content)
        print("✅ Migration executed successfully")
        print()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        await Tortoise.close_connections()
        return False
        
    # Verify results
    print("🔍 Verifying results...")
    print("-" * 60)
    
    try:
        # Check parent menu
        parent = await conn.execute_query_dict("SELECT id, name, path FROM t_sys_menu WHERE path = '/ai-monitor'")
        if parent:
            print(f"✅ Parent Menu Found: {parent[0]['name']} (ID: {parent[0]['id']})")
        else:
            print("❌ Parent Menu NOT Found")
            
        # Check child menu
        child = await conn.execute_query_dict("SELECT id, name, path, component, menu_type FROM t_sys_menu WHERE path = '/ai-monitor/model-training'")
        if child:
            print(f"✅ Child Menu Found: {child[0]['name']} (ID: {child[0]['id']})")
            print(f"   Component: {child[0]['component']}")
            print(f"   Type: {child[0]['menu_type']}")
        else:
            print("❌ Child Menu NOT Found")
            
    except Exception as e:
        print(f"⚠️ Verification failed: {e}")
        
    await Tortoise.close_connections()
    return True

if __name__ == "__main__":
    asyncio.run(execute_migration())
