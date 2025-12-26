import asyncio
import os
import asyncpg
from dotenv import load_dotenv

import json

async def verify_db():
    # Try loading .env.dev first, then .env
    if os.path.exists("app/.env.dev"):
        print("Loading app/.env.dev")
        load_dotenv("app/.env.dev")
    elif os.path.exists("app/.env"):
        print("Loading app/.env")
        load_dotenv("app/.env")
    elif os.path.exists(".env"):
        print("Loading .env")
        load_dotenv(".env")
    else:
        print("No .env file found, using defaults")
    
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "123456")
    database = os.getenv("POSTGRES_DATABASE", "device_monitor")
    
    print(f"Connecting to {user}@{host}:{port}/{database}")
    
    try:
        conn = await asyncpg.connect(
            user=user,
            password=password,
            database=database,
            host=host,
            port=port,
            ssl='disable'
        )
        print("Connected successfully.")
        
        # Check column type
        col_type = await conn.fetchval(
            """
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 't_ai_models' AND column_name = 'training_metrics'
            """
        )
        print(f"Column 'training_metrics' type: {col_type}")
        
        # Check if table exists
        # Note: to_regclass returns oid or null
        row = await conn.fetchrow(
            "SELECT to_regclass('public.t_ai_models') as table_oid"
        )
        if row and row['table_oid']:
            print("Table 't_ai_models' EXISTS.")
            
            # Count records
            count = await conn.fetchval("SELECT COUNT(*) FROM t_ai_models")
            print(f"Record count: {count}")
            
            if count > 0:
                row = await conn.fetchrow("SELECT * FROM t_ai_models LIMIT 1")
                # Print raw row to see types
                print("First record keys:", row.keys())
                tm = row['training_metrics']
                print(f"training_metrics type: {type(tm)}")
                print(f"training_metrics value: {tm}")
                
                if isinstance(tm, str):
                    try:
                        parsed = json.loads(tm)
                        print("Successfully parsed JSON string.")
                    except json.JSONDecodeError as e:
                        print(f"Failed to parse JSON string: {e}")
                
        else:
            print("Table 't_ai_models' DOES NOT EXIST!")
            
        await conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify_db())
