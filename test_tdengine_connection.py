import asyncio
import os
import sys
from datetime import datetime, timedelta

# 添加项目根目录到 pythonpath
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.tdengine_connector import TDengineConnector
from app.settings.config import TDengineCredentials

async def test_tdengine():
    try:
        # 1. 连接 TDengine
        creds = TDengineCredentials()
        print(f"Connecting to TDengine at {creds.host}:{creds.port}...")
        
        connector = TDengineConnector(
            host=creds.host,
            port=creds.port,
            user=creds.user,
            password=creds.password,
            database=creds.database
        )
        
        # 2. 检查数据库连接
        print("Checking connection...")
        try:
            # 简单的查询测试
            res = await connector.query_data("SELECT server_status()")
            print("Connection successful!")
        except Exception as e:
            print(f"Connection failed: {e}")
            return

        # 3. 检查表是否存在 (针对特定设备)
        device_code = "TestCutter02" # 替换为实际的 device_code
        potential_table_names = [
            f"tb_{device_code.lower()}",
            f"record_{device_code}",
            device_code.lower(),
            device_code
        ]
        
        found_table = None
        for name in potential_table_names:
            print(f"Checking table: {name}")
            try:
                res = await connector.query_data(f"SHOW TABLES LIKE '{name}'")
                if res and res.get('data'):
                    found_table = name
                    print(f"Found table: {found_table}")
                    break
            except Exception as e:
                print(f"Error checking table {name}: {e}")
        
        if not found_table:
            print("No table found for device.")
            # 尝试查询超级表
            print("Trying to find super table...")
            try:
                stables_res = await connector.query_data("SHOW STABLES")
                if stables_res and stables_res.get('data'):
                    print("Super tables found:", stables_res['data'])
                    # 假设第一个超级表是我们要找的
                    super_table = stables_res['data'][0][0]
                    print(f"Querying super table: {super_table} for device_code '{device_code}'")
                    
                    # 尝试通过 tag 过滤查询超级表
                    # 注意：TDengine 中 tag 列名可能不是 device_code，需要检查 schema
                    # 先获取 schema
                    desc_res = await connector.query_data(f"DESCRIBE {super_table}")
                    if desc_res and desc_res.get('data'):
                        print("Schema:", desc_res['data'])
                    
                    # 尝试查询 (假设 device_code 是 tag)
                    # count_sql = f"SELECT count(*) FROM {super_table} WHERE device_code = '{device_code}'"
                    # count_res = await connector.query_data(count_sql)
                    # print(f"Count from super table: {count_res}")
            except Exception as e:
                print(f"Error checking super tables: {e}")
            return

        # 4. 查询数据
        print(f"Querying data from {found_table}...")
        
        # 查询总数
        # 尝试使用全限定名（如果支持）或确保数据库上下文正确
        # 注意：SHOW TABLES 可能会返回表名，但在查询时可能需要数据库前缀，或者当前连接的数据库不是预期的
        # 尝试显式指定数据库名
        db_name = creds.database
        full_table_name = f"{db_name}.{found_table}"
        print(f"Trying with full table name: {full_table_name}")
        
        count_sql = f"SELECT count(*) FROM {full_table_name}"
        count_res = await connector.query_data(count_sql)
        print(f"Count result: {count_res}")
        if count_res and count_res.get('data'):
             print(f"Total count: {count_res['data'][0][0]}")
        else:
             print("Total count query returned no data.")
        
        # 查询最近数据
        query_sql = f"SELECT * FROM {full_table_name} ORDER BY ts DESC LIMIT 5"
        data_res = await connector.query_data(query_sql)
        
        if data_res and data_res.get('data'):
            print(f"Found {len(data_res['data'])} records.")
            # 打印列名
            if data_res.get('column_meta'):
                cols = [col[0] for col in data_res['column_meta']]
                print("Columns:", cols)
            
            # 打印数据
            for row in data_res['data']:
                print(row)
        else:
            print("No data found.")

        await connector.close()

    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_tdengine())
