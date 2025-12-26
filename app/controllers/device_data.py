import json
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple, Any
from decimal import Decimal

from fastapi import HTTPException
from loguru import logger
from tortoise.expressions import Q

from app.core.crud import CRUDBase
from app.models.device import DeviceInfo, DeviceType, DeviceRealTimeData
from app.models.system import SysDictData
from app.schemas.devices import DeviceRealTimeDataCreate, DeviceRealtimeQuery
from app.core.tdengine_connector import TDengineConnector
from app.core.database import get_db_connection
from app.settings.config import settings


class DeviceDataController(CRUDBase[DeviceInfo, DeviceRealTimeDataCreate, dict]):
    """设备数据控制器

    提供设备实时数据和历史数据的CRUD操作和业务逻辑处理
    """

    def __init__(self):
        super().__init__(model=DeviceRealTimeData)

    @staticmethod
    def _round_value(val: Any) -> Any:
        """
        对数值进行四舍五入保留3位小数
        支持 float 和 Decimal 类型
        """
        if isinstance(val, float):
            return round(val, 3)
        if isinstance(val, Decimal):
            return round(float(val), 3)
        return val

    async def create_realtime_data(self, obj_in: DeviceRealTimeDataCreate) -> DeviceInfo:
        """创建设备实时数据

        Args:
            obj_in: 实时数据创建对象

        Returns:
            创建的实时数据对象

        Raises:
            HTTPException: 当设备不存在或创建失败时
        """
        try:
            # 检查设备是否存在
            device = await DeviceInfo.filter(id=obj_in.device_id).first()
            if not device:
                raise HTTPException(status_code=404, detail="设备不存在")

            # 创建实时数据记录
            now = datetime.now()
            create_data = obj_in.dict()
            create_data.update({"created_at": now, "updated_at": now})

            realtime_data = await self.model.create(**create_data)

            return realtime_data

        except HTTPException:
            raise
        except Exception as e:
            import traceback

            traceback.print_exc()
            raise HTTPException(
                status_code=500, detail={"message": "创建实时数据失败", "error": str(e), "error_type": type(e).__name__}
            )

    async def get_device_latest_data(self, device_id: int) -> Optional[DeviceRealTimeData]:
        """获取设备最新实时数据

        Args:
            device_id: 设备ID

        Returns:
            最新实时数据对象或None
        """
        return await self.model.filter(device_id=device_id).order_by("-data_timestamp").first()

    async def get_device_latest_data_by_code(self, device_code: str) -> Optional[DeviceRealTimeData]:
        """根据设备编号获取最新实时数据

        Args:
            device_code: 设备编号

        Returns:
            最新实时数据对象或None
        """
        return await self.model.filter(device__device_code=device_code).order_by("-data_timestamp").first()

    async def get_devices_status_summary(self) -> List[dict]:
        """获取所有设备状态汇总

        Returns:
            设备状态汇总列表
        """
        try:
            # 获取所有设备及其最新数据
            devices = await DeviceInfo.all()
            summary = []

            for device in devices:
                latest_data = await self.get_device_latest_data(device.id)

                device_summary = {
                    "device_id": device.id,
                    "device_code": device.device_code,
                    "device_name": device.device_name,
                    "device_type": device.device_type,
                    "install_location": device.install_location,
                    "current_status": latest_data.status if latest_data else "offline",
                    "last_update": latest_data.data_timestamp if latest_data else None,
                    "voltage": latest_data.voltage if latest_data else None,
                    "current": latest_data.current if latest_data else None,
                    "power": latest_data.power if latest_data else None,
                    "temperature": latest_data.temperature if latest_data else None,
                }
                summary.append(device_summary)

            return summary

        except Exception as e:
            import traceback

            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail={"message": "获取设备状态汇总失败", "error": str(e), "error_type": type(e).__name__},
            )

    async def get_online_devices_count(self) -> int:
        """获取在线设备数量

        Returns:
            在线设备数量
        """
        # 获取最新状态为online的设备数量
        # 这里需要一个子查询来获取每个设备的最新记录
        from tortoise.query_utils import Q

        # 简化实现：获取所有设备，然后检查每个设备的最新状态
        devices = await DeviceInfo.all()
        online_count = 0

        for device in devices:
            latest_data = await self.get_device_latest_data(device.id)
            if latest_data and latest_data.status == "online":
                online_count += 1

        return online_count

    async def get_device_history_data(
        self,
        device_id: Optional[int] = None,
        device_code: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[int, List[dict]]:
        """查询设备历史数据

        Args:
            device_id: 设备ID
            device_code: 设备编号
            start_time: 开始时间
            end_time: 结束时间
            status: 设备状态
            page: 页码
            page_size: 每页数量

        Returns:
            元组(总数量, 历史数据列表)
        """
        from app.core.tdengine_connector import TDengineConnector
        from app.models.device import DeviceInfo, DeviceType
        from datetime import datetime, timezone

        logger.info(
            f"🔍 [历史数据查询] 开始查询: device_id={device_id}, device_code={device_code}, start_time={start_time}, end_time={end_time}, status={status}, page={page}, page_size={page_size}"
        )

        # 构建查询条件
        conditions = []
        table_name = None
        device_info = None

        if device_code:
            # 验证设备编号是否存在
            device_info = await DeviceInfo.filter(device_code=device_code).first()
            if not device_info:
                logger.warning(f"❌ 设备编号 {device_code} 不存在，无法查询历史数据")
                return 0, []
            
            # 准备可能的表名列表，稍后连接数据库时验证
            potential_table_names = [
                f"device_{device_code}",
                f"device_{device_code.lower()}",
                f"tb_{device_code.lower()}",
                f"record_{device_code}",
                device_code.lower(),
                device_code
            ]
            # 默认使用第一个，如果没有找到合适的，将在后续逻辑中处理
            table_name = potential_table_names[0]
            logger.info(f"✅ 设备信息: device_code={device_code}, device_type={device_info.device_type}, 待验证表名={potential_table_names}")
        else:
            logger.warning("❌ 未提供设备编号，无法查询历史数据")
            return 0, []  # 设备编号是必须的

        if start_time:
            # TDengine REST API 最好使用 ISO 8601 格式 (UTC) 以避免时区歧义
            if start_time.tzinfo:
                 start_time_str = start_time.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            else:
                 # 如果是 naive 时间，保持原样，但在 TDEngine 中可能会被解释为服务器本地时间
                 start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S.%f')
            
            conditions.append(f"ts >= '{start_time_str}'")
            logger.info(f"   时间范围: start_time={start_time_str}")
        if end_time:
            if end_time.tzinfo:
                 end_time_str = end_time.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            else:
                 end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S.%f')
            
            conditions.append(f"ts <= '{end_time_str}'")
            logger.info(f"   时间范围: end_time={end_time_str}")
        if status:
            conditions.append(f"device_status = '{status}'")

        # 添加 device_code 作为过滤条件 (用于超级表查询)
        if device_code:
             conditions.append(f"device_code = '{device_code}'")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # 获取TDengine配置并初始化连接器
        from app.settings.config import settings, TDengineCredentials

        tdengine_creds = TDengineCredentials()
        td_connector = TDengineConnector(
            host=tdengine_creds.host,
            port=tdengine_creds.port,
            user=tdengine_creds.user,
            password=tdengine_creds.password,
            database=tdengine_creds.database,
        )
        try:
            target_table = None
            
            # 1. 优先尝试从设备类型配置中获取超级表名
            if device_info and device_info.device_type:
                device_type_obj = await DeviceType.filter(type_code=device_info.device_type).first()
                if device_type_obj and device_type_obj.tdengine_stable_name:
                    # 使用反引号包裹表名，防止大小写问题
                    target_table = f"`{device_type_obj.tdengine_stable_name}`"
                    logger.info(f"✅ 从设备类型配置获取到超级表: {target_table}")
            
            # 2. 如果没找到配置的超级表，尝试之前的逻辑 (作为回退)
            if not target_table:
                # 尝试获取超级表 (旧逻辑，可能不准确)
                try:
                    stables_res = await td_connector.query_data("SHOW STABLES")
                    if stables_res and stables_res.get('data'):
                        for stable in stables_res['data']:
                            # stable[0] 是表名
                            if isinstance(stable, list) and len(stable) > 0 and isinstance(stable[0], str) and 'meters' in stable[0]:
                                target_table = f"`{stable[0]}`"
                                break
                        if not target_table and stables_res['data'] and isinstance(stables_res['data'][0], list):
                             target_table = f"`{stables_res['data'][0][0]}`"
                        
                        if target_table:
                            logger.info(f"✅ 自动发现超级表: {target_table}")
                except Exception as e:
                    logger.warning(f"⚠️ 获取超级表失败: {e}")

                # 3. 如果没找到超级表，尝试子表逻辑
                if not target_table:
                    # 检查表是否存在 (尝试多个可能的表名)
                    found_table = None
                    for name in potential_table_names:
                        # TDengine 表名可能包含特殊字符，需要用反引号包裹
                        # 但 SHOW TABLES LIKE 不需要包裹，它匹配的是字符串
                        check_table_sql = f"SHOW TABLES LIKE '{name}'"
                        logger.info(f"🔍 检查表是否存在: {check_table_sql}")
                        try:
                            table_check_result = await td_connector.query_data(check_table_sql)
                            if table_check_result and table_check_result.get('data'):
                                # 确保找到的表名是正确的
                                found_table = name
                                logger.info(f"✅ 找到表: {found_table}")
                                break
                        except Exception as e:
                            logger.warning(f"⚠️ 检查表 {name} 失败: {e}")
                    
                    if found_table:
                        # 构造查询时，表名必须加反引号，特别是当表名包含连字符时
                        target_table = f"`{found_table}`"
                        # 如果是具体子表，不需要 device_code 过滤条件
                        conditions_sub = [c for c in conditions if not c.startswith("device_code =")]
                        where_clause = " AND ".join(conditions_sub) if conditions_sub else "1=1"
            
            if not target_table:
                logger.warning(f"❌ 未找到可查询的表 (超级表或子表)")
                await td_connector.close()
                return 0, []
            
            table_name = target_table
            logger.info(f"🚀 最终查询表名: {table_name}, 条件: {where_clause}")
            
            # 使用 SELECT * 查询所有字段
            # 对于历史曲线图 (page_size >= 1000)，按时间正序排列，并限制返回数量防止超时
            # 对于表格视图，按时间倒序排列，支持分页
            if page_size >= 1000:
                # 图表模式：跳过Count查询以提高性能，且限制最大返回数量
                total_count = 0 
                # 安全限制：即使是图表模式，也限制最大返回数量（例如 page_size 或 5000）
                # 这里使用传入的 page_size 作为限制，前端应负责传入合适的大小
                limit = page_size
                query_sql = f"SELECT * FROM {table_name} WHERE {where_clause} ORDER BY ts ASC LIMIT {limit}"
                logger.info(f"🔍 执行查询（图表模式 - 限制{limit}条）: {query_sql}")
            else:
                # 表格模式：需要Count查询
                count_sql = f"SELECT count(*) FROM {table_name} WHERE {where_clause}"
                logger.info(f"🔍 查询总数: {count_sql}")
                count_result = await td_connector.query_data(count_sql)
                total_count = count_result["data"][0][0] if count_result and count_result.get("data") else 0
                logger.info(f"✅ 总记录数: {total_count}")

                if total_count == 0:
                    logger.warning(f"⚠️ 没有找到符合条件的历史数据")
                    await td_connector.close()
                    return 0, []

                # 构建分页查询
                offset = (page - 1) * page_size
                limit = page_size
                query_sql = f"SELECT * FROM {table_name} WHERE {where_clause} ORDER BY ts DESC LIMIT {limit} OFFSET {offset}"
                logger.info(f"🔍 执行分页查询（表格模式）: {query_sql}")

            query_result = await td_connector.query_data(query_sql)
            
            # 处理查询结果
            result_list = []
            if query_result and query_result.get("data"):
                records = query_result["data"]
                column_meta = query_result.get("column_meta", [])
                
                # 从column_meta提取列名
                if column_meta:
                    column_names = [col[0] for col in column_meta]
                    logger.info(f"✅ 查询到 {len(records)} 条记录，字段: {column_names}")
                    
                    for record in records:
                        record_dict = dict(zip(column_names, record))
                        # 确保ts字段存在
                        if 'ts' in record_dict:
                            record_dict["data_timestamp"] = record_dict["ts"]
                        result_list.append(record_dict)
                else:
                    logger.warning("⚠️ 查询结果没有column_meta信息")
            else:
                logger.warning(f"⚠️ 查询结果为空或格式不正确: {query_result}")

            await td_connector.close()
            logger.info(f"✅ 历史数据查询完成: 返回 {len(result_list)} 条记录")
            return total_count, result_list

        except Exception as e:
            logger.error(f"❌ 查询设备历史数据失败: {e}", exc_info=True)
            await td_connector.close()
            raise HTTPException(status_code=500, detail=f"查询设备历史数据失败: {e}")

    async def update_device_realtime_data(self, device_id: int, data: dict) -> DeviceRealTimeData:
        """更新设备实时数据（覆盖式更新）

        Args:
            device_id: 设备ID
            data: 更新数据

        Returns:
            更新后的实时数据对象
        """
        try:
            # 检查设备是否存在
            device = await DeviceInfo.filter(id=device_id).first()
            if not device:
                raise HTTPException(status_code=404, detail="设备不存在")

            # 获取或创建实时数据记录
            realtime_data = await self.get_device_latest_data(device_id)

            now = datetime.now()
            data.update({"updated_at": now, "data_timestamp": now})

            if realtime_data:
                # 更新现有记录
                await self.model.filter(id=realtime_data.id).update(**data)
                realtime_data = await self.model.filter(id=realtime_data.id).first()
            else:
                # 创建新记录
                data.update({"device_id": device_id, "created_at": now})
                realtime_data = await self.model.create(**data)

            # 同时创建历史数据记录
            history_data = data.copy()
            history_data.update({"device_id": device_id, "created_at": now})
            await DeviceHistoryData.create(**history_data)

            return realtime_data

        except HTTPException:
            raise
        except Exception as e:
            import traceback

            traceback.print_exc()
            raise HTTPException(
                status_code=500, detail={"message": "更新实时数据失败", "error": str(e), "error_type": type(e).__name__}
            )

    async def get_device_realtime_data(self, query: DeviceRealtimeQuery, td_connector: Optional[TDengineConnector] = None) -> dict:
        """
        获取设备实时数据

        Args:
            query: 查询参数，包含分页、设备代码等信息
            td_connector: 复用的TDengine连接器（可选）

        Returns:
            dict: 包含设备实时数据的字典
        """
        if query.paged:
            return await self._get_device_realtime_data_paged(query, td_connector)
        else:
            return await self._get_device_realtime_data_unpaged(query, td_connector)

    async def _get_device_realtime_data_unpaged(self, query: DeviceRealtimeQuery, td_connector: Optional[TDengineConnector] = None) -> dict:
        """
        获取设备实时数据（旧版-全量查询）
        """
        should_close_connector = False
        if not td_connector:
            # 初始化TDengine连接器
            from app.settings.config import TDengineCredentials

            tdengine_creds = TDengineCredentials()
            logger.info(
                f"初始化TDengine连接器: host={tdengine_creds.host}, port={tdengine_creds.port}, database={tdengine_creds.database}"
            )
            tdengine_connector = TDengineConnector(
                host=tdengine_creds.host,
                port=tdengine_creds.port,
                user=tdengine_creds.user,
                password=tdengine_creds.password,
                database=tdengine_creds.database,
            )
            should_close_connector = True
            logger.info("TDengine连接器初始化完成")

        try:
            # 验证设备存在性（如果指定了device_code或device_codes）
            if query.device_code:
                device_exists = await DeviceInfo.filter(
                    device_code=query.device_code, device_type=query.type_code
                ).exists()
                if not device_exists:
                    raise HTTPException(status_code=404, detail=f"设备 {query.device_code} 不存在或类型不匹配")
            elif query.device_codes:
                # 验证设备编码列表中的设备是否存在
                existing_devices = await DeviceInfo.filter(
                    device_code__in=query.device_codes, device_type=query.type_code
                ).values_list("device_code", flat=True)

                missing_devices = set(query.device_codes) - set(existing_devices)
                if missing_devices:
                    raise HTTPException(
                        status_code=404, detail=f"以下设备不存在或类型不匹配: {', '.join(missing_devices)}"
                    )

            # 根据type_code查询对应类型的设备信息
            # 1. 从PostgreSQL查询指定类型的设备
            device_filter = {}
            # 如果指定了 type_code 且不是 "all"，则按类型过滤
            if query.type_code and query.type_code != "all":
                device_filter["device_type"] = query.type_code
            
            if query.device_code:
                device_filter["device_code"] = query.device_code
            elif query.device_codes:
                device_filter["device_code__in"] = query.device_codes

            devices = await DeviceInfo.filter(**device_filter).all()

            if not devices:
                return {
                    "items": [],
                    "total": 0,
                    "page": query.page,
                    "page_size": query.page_size,
                    "type_code": query.type_code,
                }

            # 2. 计算分页范围
            total_devices = len(devices)
            start_index = (query.page - 1) * query.page_size
            end_index = start_index + query.page_size

            # 3. 获取当前页的设备列表
            current_page_devices = devices[start_index:end_index]

            # 4. 批量从TDengine查询实时数据（性能优化）
            realtime_data_list = []

            # 初始化TDengine连接器（移到循环外）
            # from app.settings.config import TDengineCredentials
            # tdengine_creds = TDengineCredentials()
            # tdengine_connector = TDengineConnector(...)
            # logger.info("TDengine连接器初始化完成")

            # 判断是查询单一设备类型还是所有设备类型
            if query.type_code and query.type_code != "all":
                # 查询单一设备类型
                device_type_obj = await DeviceType.filter(type_code=query.type_code, is_active=True).first()
                if not device_type_obj:
                    # 不要抛出异常，而是返回空数据（避免WebSocket连接关闭）
                    logger.warning(f"设备类型 {query.type_code} 不存在或未激活，返回空数据")
                    if should_close_connector:
                        await tdengine_connector.close()
                    return {
                        "items": [],
                        "total": 0,
                        "page": query.page,
                        "page_size": query.page_size,
                        "type_code": query.type_code,
                        "error": f"设备类型 {query.type_code} 不存在或未激活"
                    }
                
                super_table_name = device_type_obj.tdengine_stable_name
                logger.info(f"使用TDengine超级表: {super_table_name} (设备类型: {query.type_code})")
            else:
                # 查询所有设备类型，需要按设备类型分组
                super_table_name = None
                logger.info("查询所有设备类型，将按设备类型分组查询")

            # 查询 TDengine 数据
            device_data_map = {}
            
            if current_page_devices:
                try:
                    if super_table_name:
                        # 统一使用 device_code 作为 tag 列名
                        tag_col = "device_code"
                        # 移除对 plasma_cutter_2025 的特殊处理，统一规范
                        # if super_table_name == "plasma_cutter_2025":
                        #     tag_col = "device_id"

                        # 单一设备类型查询
                        where_clause = ""
                        if query.device_codes:
                            codes_str = ", ".join([f"'{code}'" for code in query.device_codes])
                            where_clause = f"WHERE {tag_col} IN ({codes_str})"
                        elif query.device_code:
                            where_clause = f"WHERE {tag_col} = '{query.device_code}'"

                        if where_clause:
                            batch_sql = f"SELECT LAST_ROW(*), {tag_col} FROM `{super_table_name}` {where_clause} GROUP BY {tag_col}"
                        else:
                            batch_sql = f"SELECT LAST_ROW(*), {tag_col} FROM `{super_table_name}` GROUP BY {tag_col}"

                        logger.info(f"准备执行TDengine超级表查询")
                        logger.debug(f"超级表查询SQL: {batch_sql}")
                        
                        raw_result = await tdengine_connector.execute_sql(batch_sql, target_db=tdengine_creds.database)
                        if isinstance(raw_result, dict) and "data" in raw_result and "column_meta" in raw_result:
                            columns = [col[0] for col in raw_result["column_meta"]]
                            rows = raw_result["data"]
                            for row in rows:
                                row_dict = dict(zip(columns, row))
                                # Map tag_col back to device_code for internal logic
                                device_code_val = row_dict.get(tag_col)
                                if device_code_val:
                                    device_data_map[device_code_val] = row_dict
                                else:
                                    logger.warning(f"Row data missing {tag_col}: {row_dict}. This row will be skipped.")
                    else:
                        # 多设备类型查询：按设备类型分组
                        logger.info("按设备类型分组查询TDengine数据")
                        
                        # 按设备类型分组
                        devices_by_type = {}
                        for device in current_page_devices:
                            device_type = device.device_type
                            if device_type not in devices_by_type:
                                devices_by_type[device_type] = []
                            devices_by_type[device_type].append(device)
                        
                        # 分别查询每种设备类型
                        for device_type, type_devices in devices_by_type.items():
                            device_type_obj = await DeviceType.filter(type_code=device_type, is_active=True).first()
                            if not device_type_obj:
                                logger.warning(f"设备类型 {device_type} 不存在或未激活，跳过")
                                continue
                            
                            type_super_table = device_type_obj.tdengine_stable_name
                            
                            # 统一使用 device_code 作为 tag 列名
                            tag_col = "device_code"
                            # 移除对 plasma_cutter_2025 的特殊处理
                            # if type_super_table == "plasma_cutter_2025":
                            #     tag_col = "device_id"
                            
                            device_codes_for_type = [d.device_code for d in type_devices]
                            codes_str = ", ".join([f"'{code}'" for code in device_codes_for_type])
                            
                            type_sql = f"SELECT LAST_ROW(*), {tag_col} FROM `{type_super_table}` WHERE {tag_col} IN ({codes_str}) GROUP BY {tag_col}"
                            logger.debug(f"查询设备类型 {device_type} 的SQL: {type_sql}")
                            
                            type_result = await tdengine_connector.execute_sql(type_sql, target_db=tdengine_creds.database)
                            if isinstance(type_result, dict) and "data" in type_result and "column_meta" in type_result:
                                columns = [col[0] for col in type_result["column_meta"]]
                                rows = type_result["data"]
                                for row in rows:
                                    row_dict = dict(zip(columns, row))
                                    # Map tag_col back to device_code for internal logic
                                    device_code_val = row_dict.get(tag_col)
                                    if device_code_val:
                                        device_data_map[device_code_val] = row_dict

                    # 辅助函数：从 TDengine 结果中提取字段值
                    def get_field_value(row_data, field_name):
                        if field_name in row_data:
                            return row_data.get(field_name)
                        last_row_field = f"last_row({field_name})"
                        if last_row_field in row_data:
                            return row_data.get(last_row_field)
                        return None
                    
                    # 处理每个设备的数据
                    for device in current_page_devices:
                        row_data = device_data_map.get(device.device_code)
                        if row_data:
                            # 动态提取所有字段（除了特殊字段）
                            data_fields = {}
                            # 特殊字段：不需要作为监测数据的字段
                            special_fields = {'device_code', 'device_name', 'name', 'install_location', 'ts'}
                            
                            for field_name in row_data.keys():
                                # 处理 last_row() 包装的字段
                                if field_name.startswith('last_row(') and field_name.endswith(')'):
                                    # 提取字段名（去掉 last_row() 前缀）
                                    actual_field_name = field_name[9:-1]  # 去掉 'last_row(' 和 ')'
                                    if actual_field_name not in special_fields:
                                        val = row_data[field_name]
                                        val = self._round_value(val)
                                        data_fields[actual_field_name] = val
                                        logger.debug(f"提取字段: {field_name} -> {actual_field_name} = {val}")
                                # 处理普通字段
                                elif field_name not in special_fields:
                                    val = row_data[field_name]
                                    val = self._round_value(val)
                                    data_fields[field_name] = val
                                    logger.debug(f"提取字段: {field_name} = {val}")
                            
                            # 提取时间戳
                            ts_value = get_field_value(row_data, "ts")
                            ts_formatted = str(ts_value) if ts_value else None

                            # 构建设备数据
                            # 优先从TDengine获取device_name，如果没有则使用PostgreSQL中的设备名称
                            tdengine_device_name = get_field_value(row_data, "device_name") or get_field_value(row_data, "name")
                            device_data = {
                                "device_code": device.device_code,
                                "device_name": tdengine_device_name or device.device_name or "",
                                "type_code": device.device_type,  # 使用设备实际的类型
                                "ts": ts_formatted,
                                "device_status": data_fields.get("device_status", "online"),
                            }
                            device_data.update(data_fields)
                            logger.debug(f"设备 {device.device_code} 的完整数据: {device_data}")
                            realtime_data_list.append(device_data)
                        else:
                            # 没有 TDengine 数据的设备，尝试从 PostgreSQL 获取
                            latest_pg_data = await DeviceRealTimeData.filter(device_id=device.id).order_by('-data_timestamp').first()
                            
                            if latest_pg_data:
                                metrics = latest_pg_data.metrics or {}
                                # 对 metrics 中的数值进行四舍五入
                                for k, v in metrics.items():
                                    metrics[k] = self._round_value(v)
                                    
                                device_data = {
                                    "device_code": device.device_code,
                                    "device_name": device.device_name or "",
                                    "type_code": device.device_type,
                                    "ts": latest_pg_data.data_timestamp.isoformat() if latest_pg_data.data_timestamp else None,
                                    "device_status": latest_pg_data.status or "offline",
                                }
                                device_data.update(metrics)
                            else:
                                # PostgreSQL 也没有数据
                                device_data = {
                                    "device_code": device.device_code,
                                    "device_name": device.device_name or "",
                                    "type_code": device.device_type,
                                    "ts": None,
                                    "device_status": "offline",
                                }
                            realtime_data_list.append(device_data)
                except Exception as device_error:
                    logger.error(f"处理设备实时数据时发生错误: {str(device_error)}", exc_info=True)
                    for device_in_page in current_page_devices:
                        # 尝试从 PostgreSQL 获取最新数据
                        try:
                            latest_pg_data = await DeviceRealTimeData.filter(device_id=device_in_page.id).order_by('-data_timestamp').first()
                        except Exception:
                            latest_pg_data = None
                            
                        if latest_pg_data:
                            metrics = latest_pg_data.metrics or {}
                            # 对 metrics 中的数值进行四舍五入
                            for k, v in metrics.items():
                                metrics[k] = self._round_value(v)
                                
                            device_data = {
                                "device_code": device_in_page.device_code,
                                "device_name": device_in_page.device_name or "",
                                "type_code": query.type_code,
                                "ts": latest_pg_data.data_timestamp.isoformat() if latest_pg_data.data_timestamp else None,
                                "device_status": latest_pg_data.status or "error",
                            }
                            device_data.update(metrics)
                        else:
                            device_data = {
                                "device_code": device_in_page.device_code,
                                "device_name": device_in_page.device_name or "",
                                "type_code": query.type_code,
                                "ts": None,
                                "device_status": "error",
                            }
                        realtime_data_list.append(device_data)

            await tdengine_connector.close()

            return {
                "items": realtime_data_list,
                "total": total_devices,
                "page": query.page,
                "page_size": query.page_size,
                "type_code": query.type_code,
            }
        except Exception as e:
            logger.error(f"获取设备实时数据失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"message": "获取设备实时数据失败", "error": str(e), "error_type": type(e).__name__},
            )

    async def _get_device_realtime_data_paged(self, query: DeviceRealtimeQuery, td_connector: Optional[TDengineConnector] = None) -> dict:
        """
        获取设备实时数据（新版-分页优化）
        """
        should_close_connector = False
        if not td_connector:
            from app.settings.config import TDengineCredentials

            tdengine_creds = TDengineCredentials()
            tdengine_connector = TDengineConnector(
                host=tdengine_creds.host,
                port=tdengine_creds.port,
                user=tdengine_creds.user,
                password=tdengine_creds.password,
                database=tdengine_creds.database,
            )
            should_close_connector = True

        try:
            # 1. 构建基础查询，并应用分页
            device_query = DeviceInfo.filter(device_type=query.type_code)
            if query.device_code:
                device_query = device_query.filter(device_code=query.device_code)
            elif query.device_codes:
                device_query = device_query.filter(device_code__in=query.device_codes)

            total_devices = await device_query.count()

            # 在数据库层面进行分页
            current_page_devices = await device_query.offset((query.page - 1) * query.page_size).limit(query.page_size)

            if not current_page_devices:
                return {
                    "items": [],
                    "total": 0,
                    "page": query.page,
                    "page_size": query.page_size,
                    "type_code": query.type_code,
                }

            # 2. 仅针对当前页的设备查询TDengine
            device_codes_for_tdengine = [d.device_code for d in current_page_devices]
            realtime_data_list = []

            from app.settings.config import TDengineCredentials

            tdengine_creds = TDengineCredentials()
            tdengine_connector = TDengineConnector(
                host=tdengine_creds.host,
                port=tdengine_creds.port,
                user=tdengine_creds.user,
                password=tdengine_creds.password,
                database=tdengine_creds.database,
            )

            # 根据设备类型获取对应的TDengine超级表名
            device_type_obj = await DeviceType.filter(type_code=query.type_code, is_active=True).first()
            if not device_type_obj:
                raise HTTPException(status_code=404, detail=f"设备类型 {query.type_code} 不存在或未激活")
            
            super_table_name = device_type_obj.tdengine_stable_name
            logger.info(f"使用TDengine超级表: {super_table_name} (设备类型: {query.type_code})")
            
            # 统一使用 device_code 作为 tag 列名
            tag_col = "device_code"
            # 移除对 plasma_cutter_2025 的特殊处理
            # if super_table_name == "plasma_cutter_2025":
            #     tag_col = "device_id"
                
            codes_str = ", ".join([f"'{code}'" for code in device_codes_for_tdengine])
            where_clause = f"WHERE {tag_col} IN ({codes_str})"

            batch_sql = f"SELECT LAST_ROW(*), {tag_col} FROM `{super_table_name}` {where_clause} GROUP BY {tag_col}"
            logger.debug(f"PAGED - TDengine SQL: {batch_sql}")

            raw_result = await tdengine_connector.execute_sql(batch_sql, target_db=tdengine_creds.database)

            device_data_map = {}
            if isinstance(raw_result, dict) and "data" in raw_result and "column_meta" in raw_result:
                columns = [col[0] for col in raw_result["column_meta"]]
                for row in raw_result["data"]:
                    row_dict = dict(zip(columns, row))
                    # Map tag_col back to device_code for internal logic
                    device_code_val = row_dict.get(tag_col)
                    if device_code_val:
                        device_data_map[device_code_val] = row_dict

            # 3. 合并数据
            for device in current_page_devices:
                row_data = device_data_map.get(device.device_code)
                
                # 检查TDengine数据有效性：必须有时间戳
                is_valid_td_data = False
                if row_data:
                    ts_check = row_data.get("ts") or row_data.get("last_row(ts)")
                    if ts_check:
                        is_valid_td_data = True
                    else:
                        logger.warning(f"TDengine返回了无效数据(无时间戳): device={device.device_code}")

                if is_valid_td_data:

                    def get_field_value(row_data, field_name):
                        return row_data.get(field_name) or row_data.get(f"last_row({field_name})")

                    # 动态提取所有字段（除了特殊字段）
                    data_fields = {}
                    special_fields = {'device_code', 'device_name', 'name', 'install_location', 'ts'}
                    
                    for field_name in row_data.keys():
                        # 处理 last_row() 包装的字段
                        if field_name.startswith('last_row(') and field_name.endswith(')'):
                            # 提取字段名（去掉 last_row() 前缀）
                            actual_field_name = field_name[9:-1]  # 去掉 'last_row(' 和 ')'
                            if actual_field_name not in special_fields:
                                val = row_data[field_name]
                                val = self._round_value(val)
                                data_fields[actual_field_name] = val
                        # 处理普通字段
                        elif field_name not in special_fields:
                            val = row_data[field_name]
                            val = self._round_value(val)
                            data_fields[field_name] = val
                    
                    ts_value = get_field_value(row_data, "ts")
                    # 从TDengine的device_name标签获取设备名称，如果没有则使用PostgreSQL中的设备名称
                    tdengine_name = get_field_value(row_data, "device_name") or get_field_value(row_data, "name") or device.device_name or ""

                    device_data = {
                        "device_code": device.device_code,
                        "device_name": tdengine_name,
                        "type_code": query.type_code,
                        "ts": str(ts_value) if ts_value else None,
                        "device_status": data_fields.get("device_status", "online"),
                        **data_fields,
                    }
                    realtime_data_list.append(device_data)
                else:
                    # TDengine中无数据，尝试从 PostgreSQL 获取
                    logger.info(f"TDengine无数据，尝试查询PG: device_id={device.id}, code={device.device_code}")
                    latest_pg_data = await DeviceRealTimeData.filter(device_id=device.id).order_by('-data_timestamp').first()
                    logger.info(f"PG查询结果: {latest_pg_data}, metrics={latest_pg_data.metrics if latest_pg_data else 'None'}")
                    
                    if latest_pg_data:
                        metrics = latest_pg_data.metrics or {}
                        # 对 metrics 中的数值进行四舍五入
                        for k, v in metrics.items():
                            metrics[k] = self._round_value(v)
                            
                        device_data = {
                            "device_code": device.device_code,
                            "device_name": device.device_name or "",
                            "type_code": query.type_code,
                            "ts": latest_pg_data.data_timestamp.isoformat() if latest_pg_data.data_timestamp else None,
                            "device_status": latest_pg_data.status or "offline",
                        }
                        device_data.update(metrics)
                    else:
                        # PostgreSQL 也没有数据
                        device_data = {
                            "device_code": device.device_code,
                            "device_name": device.device_name or "",
                            "type_code": query.type_code,
                            "ts": None,
                            "device_status": "offline",
                        }
                    realtime_data_list.append(device_data)

            return {
                "items": realtime_data_list,
                "total": total_devices,
                "page": query.page,
                "page_size": query.page_size,
                "type_code": query.type_code,
            }
        except Exception as e:
            logger.error(f"获取设备实时数据失败(分页): {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail={"message": "获取设备实时数据失败(分页)", "error": str(e)})
        finally:
            if 'tdengine_connector' in locals() and tdengine_connector and should_close_connector:
                await tdengine_connector.close()

    async def get_realtime_device_status(self, device_type: str) -> dict:
        """获取指定类型设备的实时状态统计

        从一个包含聚合数据的普通表中获取最新一条记录。

        Args:
            device_type: 设备类型代码 (e.g., 'welding')

        Returns:
            设备实时状态统计字典
        """
        tdengine_connector = None
        try:
            logger.info(f"开始获取设备聚合状态，类型: {device_type}")
            db_name = "hlzg_db"

            # 从数据字典获取表名
            dict_entry = await SysDictData.filter(dict_type__type_code='welding_indicator_mapping', data_label='实时状态统计').first()
            if not dict_entry:
                logger.error("未找到数据字典中'焊机统计指标对照'类型下'实时状态统计'的配置。")
                return {
                    "total_devices": 0,
                    "standby_devices": 0,
                    "welding_devices": 0,
                    "alarm_devices": 0,
                    "shutdown_devices": 0,
                    "standby_rate": 0.0,
                    "welding_rate": 0.0,
                    "alarm_rate": 0.0,
                    "shutdown_rate": 0.0,
                    "last_update_time": None,
                }
            table_name = dict_entry.data_value
            logger.debug(f"目标表名: {table_name}，数据库: {db_name}")

            from app.settings.config import TDengineCredentials

            tdengine_creds = TDengineCredentials()

            tdengine_connector = TDengineConnector(
                host=tdengine_creds.host,
                port=tdengine_creds.port,
                user=tdengine_creds.user,
                password=tdengine_creds.password,
                database=tdengine_creds.database,
            )

            # 使用 last_row(*) 查询获取最新数据
            query_sql = f"SELECT last_row(*) FROM {table_name}"

            logger.info(f"准备执行TDengine查询: {query_sql} on database {db_name}")
            result = await tdengine_connector.execute_sql(query_sql, target_db=db_name)
            logger.info("TDengine查询执行完毕。")
            logger.debug(f"TDengine返回的原始结果: {result}")

            # last_row(*) 返回的数据结构需要解析
            logger.info(f"检查TDengine结果: result存在={bool(result)}, data存在={bool(result and result.get('data'))}, column_meta存在={bool(result and result.get('column_meta'))}")
            logger.info(f"result类型: {type(result)}, result内容: {result}")
            
            # 详细检查每个条件
            result_exists = bool(result)
            data_exists = bool(result and result.get('data'))
            column_meta_exists = bool(result and result.get('column_meta'))
            
            logger.info(f"条件检查详情: result_exists={result_exists}, data_exists={data_exists}, column_meta_exists={column_meta_exists}")
            
            if not (result and result.get("data") and result.get("column_meta")):
                logger.warning(f"在表 {table_name} 中未找到任何数据，返回全0结果")
                return {
                    "total_devices": 0,
                    "standby_devices": 0,
                    "welding_devices": 0,
                    "alarm_devices": 0,
                    "shutdown_devices": 0,
                    "standby_rate": 0.0,
                    "welding_rate": 0.0,
                    "alarm_rate": 0.0,
                    "shutdown_rate": 0.0,
                    "last_update_time": None,
                }

            # 将列名和数据行组合成字典
            columns = [meta[0] for meta in result["column_meta"]]
            row_values = result["data"][0]
            latest_data = dict(zip(columns, row_values))
            
            logger.info(f"解析后的数据字典: {latest_data}")

            # 从带有 'last_row()' 前缀的键中获取数据
            # 根据实际表结构获取数据
            standby_devices = int(latest_data.get("last_row(status_standby)", 0))
            welding_devices = int(latest_data.get("last_row(status_welding)", 0))
            alarm_devices = int(latest_data.get("last_row(status_alarm)", 0))
            shutdown_devices = int(latest_data.get("last_row(status_shutdown)", 0))
            last_update_time = latest_data.get("last_row(ts)")
            
            logger.info(f"解析的设备数量 - standby: {standby_devices}, welding: {welding_devices}, alarm: {alarm_devices}, shutdown: {shutdown_devices}")
            
            # 计算总设备数
            total_devices = standby_devices + welding_devices + alarm_devices + shutdown_devices
            logger.info(f"计算的总设备数: {total_devices}")
            
            # 计算总设备数
            total_devices = standby_devices + welding_devices + alarm_devices + shutdown_devices

            # 计算比率
            standby_rate = (standby_devices / total_devices * 100) if total_devices > 0 else 0.0
            welding_rate = (welding_devices / total_devices * 100) if total_devices > 0 else 0.0
            alarm_rate = (alarm_devices / total_devices * 100) if total_devices > 0 else 0.0
            shutdown_rate = (shutdown_devices / total_devices * 100) if total_devices > 0 else 0.0

            # 处理时间戳格式
            formatted_time = None
            if last_update_time:
                try:
                    # 如果是datetime对象，直接转换
                    if hasattr(last_update_time, 'isoformat'):
                        formatted_time = last_update_time.isoformat()
                    else:
                        # 如果是字符串，直接使用
                        formatted_time = str(last_update_time)
                except Exception as time_error:
                    logger.warning(f"时间戳格式转换失败: {time_error}, 原始值: {last_update_time}")
                    formatted_time = str(last_update_time)

            return {
                "total_devices": total_devices,
                "standby_devices": standby_devices,
                "welding_devices": welding_devices,
                "alarm_devices": alarm_devices,
                "shutdown_devices": shutdown_devices,
                "standby_rate": round(standby_rate, 1),
                "welding_rate": round(welding_rate, 1),
                "alarm_rate": round(alarm_rate, 1),
                "shutdown_rate": round(shutdown_rate, 1),
                "last_update_time": formatted_time,
            }



        except Exception as e:
            logger.error(f"获取设备聚合状态时发生严重错误: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500, detail={"message": f"获取设备实时状态失败: {e}", "error_type": type(e).__name__}
            )
        finally:
            if tdengine_connector:
                await tdengine_connector.close()

    async def get_device_status_statistics(self, type_code: Optional[str] = None) -> dict:
        """获取设备状态统计信息

        直接从TDengine的hlzg_db.welding_status_real_summary表获取实时汇总数据

        Args:
            type_code: 设备类型代码，暂时保留参数但不使用（汇总表是全局统计）

        Returns:
            设备状态统计字典
        """
        try:
            # 获取TDengine配置并初始化连接器
            from app.settings.config import TDengineCredentials

            tdengine_creds = TDengineCredentials()
            tdengine_connector = TDengineConnector(
                host=tdengine_creds.host,
                port=tdengine_creds.port,
                user=tdengine_creds.user,
                password=tdengine_creds.password,
                database=tdengine_creds.database,
            )

            # 查询最新的设备状态汇总数据
            query_sql = """
                SELECT status_standby, status_welding, status_alarm, status_shutdown, ts
                FROM hlzg_db.welding_status_real_summary 
                WHERE name='welding_status_real_summary' 
                ORDER BY ts DESC 
                LIMIT 1
            """

            logger.info(f"执行TDengine查询: {query_sql}")
            result = await tdengine_connector.execute_sql(query_sql)

            # 关闭TDengine连接
            await tdengine_connector.close()

            # 解析TDengine REST API响应格式
            data_rows = []
            if isinstance(result, dict) and "data" in result:
                data_rows = result["data"]
            elif isinstance(result, list):
                data_rows = result

            if not data_rows or len(data_rows) == 0:
                logger.warning("未找到设备状态汇总数据")
                return {
                    "total_devices": 0,
                    "standby_devices": 0,
                    "welding_devices": 0,
                    "alarm_devices": 0,
                    "shutdown_devices": 0,
                    "standby_rate": 0.0,
                    "welding_rate": 0.0,
                    "alarm_rate": 0.0,
                    "shutdown_rate": 0.0,
                    "last_update_time": None,
                }

            # 解析查询结果
            row = data_rows[0]
            standby_count = int(row[0]) if row[0] is not None else 0
            welding_count = int(row[1]) if row[1] is not None else 0
            alarm_count = int(row[2]) if row[2] is not None else 0
            shutdown_count = int(row[3]) if row[3] is not None else 0
            last_update_time = row[4] if row[4] is not None else None

            # 计算总设备数
            total_devices = standby_count + welding_count + alarm_count + shutdown_count

            # 计算各状态占比
            if total_devices > 0:
                standby_rate = round(standby_count / total_devices * 100, 1)
                welding_rate = round(welding_count / total_devices * 100, 1)
                alarm_rate = round(alarm_count / total_devices * 100, 1)
                shutdown_rate = round(shutdown_count / total_devices * 100, 1)
            else:
                standby_rate = welding_rate = alarm_rate = shutdown_rate = 0.0

            return {
                "total_devices": total_devices,
                "standby_devices": standby_count,
                "welding_devices": welding_count,
                "alarm_devices": alarm_count,
                "shutdown_devices": shutdown_count,
                "standby_rate": standby_rate,
                "welding_rate": welding_rate,
                "alarm_rate": alarm_rate,
                "shutdown_rate": shutdown_rate,
                "last_update_time": str(last_update_time) if last_update_time else None,
            }

        except Exception as e:
            logger.error(f"获取设备状态统计失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"message": "获取设备状态统计失败", "error": str(e), "error_type": type(e).__name__},
            )

    async def get_device_online_rate_history(self, type_code: Optional[str] = None, days: int = 7) -> List[dict]:
        """获取设备在线率历史数据

        Args:
            type_code: 设备类型代码，不提供则查询所有类型
            days: 查询天数，默认7天

        Returns:
            在线率历史数据列表
        """
        try:
            from datetime import datetime, timedelta
            import asyncio

            # 计算查询时间范围
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days - 1)

            # 构建设备查询条件
            device_filter = {}
            if type_code:
                device_filter["device_type"] = type_code

            devices = await DeviceInfo.filter(**device_filter).all()
            total_devices = len(devices)

            if total_devices == 0:
                return []

            # 生成日期列表
            date_list = []
            current_date = start_date
            while current_date <= end_date:
                date_list.append(current_date)
                current_date += timedelta(days=1)

            # 为每一天计算在线率
            history_data = []
            for date in date_list:
                # 简化实现：使用当前状态作为历史数据
                # 在实际项目中，应该查询历史数据表或时序数据库
                online_count = 0
                for device in devices:
                    latest_data = await self.get_device_latest_data(device.id)
                    if latest_data and latest_data.status and latest_data.status.lower() == "online":
                        online_count += 1

                online_rate = round(online_count / total_devices * 100, 1) if total_devices > 0 else 0
                history_data.append(
                    {
                        "date": date.strftime("%m月%d日"),
                        "online_rate": online_rate,
                        "online_count": online_count,
                        "total_count": total_devices,
                    }
                )

            return history_data

        except Exception as e:
            logger.error(f"获取设备在线率历史数据失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"message": "获取设备在线率历史数据失败", "error": str(e), "error_type": type(e).__name__},
            )

    async def get_online_rate_statistics(
        self,
        device_type: Optional[str] = None,
        device_group: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[dict]:
        """获取在线率统计数据
        
        从TDengine查询在线率统计数据
        
        Args:
            device_type: 设备类型代码
            device_group: 设备组
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            
        Returns:
            在线率统计数据列表，每个元素包含一天的数据
        """
        tdengine_connector = None
        try:
            from datetime import datetime, timedelta
            from app.settings.config import TDengineCredentials
            
            logger.info(f"获取在线率统计数据 - 设备类型: {device_type}, 设备组: {device_group}, 开始日期: {start_date}, 结束日期: {end_date}")
            
            # 解析日期范围
            if start_date and end_date:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            else:
                # 默认查询最近7天
                end_dt = datetime.now()
                start_dt = end_dt - timedelta(days=6)
            
            # 初始化TDengine连接
            tdengine_creds = TDengineCredentials()
            tdengine_connector = TDengineConnector(
                host=tdengine_creds.host,
                port=tdengine_creds.port,
                user=tdengine_creds.user,
                password=tdengine_creds.password,
                database=tdengine_creds.database,
            )
            
            # 根据 device_type 动态选择表名
            from app.models.system import SysDictData
            table_name = ""
            if device_type == "welding":
                dict_entry = await SysDictData.filter(dict_type__type_code='welding_indicator_mapping', data_label='焊机数据表').first()
                if dict_entry:
                    table_name = dict_entry.data_value
                else:
                    logger.error("未找到数据字典中'welding_indicator_mapping'类型下'焊机数据表'的配置。")
                    raise HTTPException(status_code=500, detail="未找到焊机数据表配置")
            else:
                # 对于其他 device_type，可以添加相应的映射逻辑或抛出错误
                logger.error(f"不支持的设备类型: {device_type}")
                raise HTTPException(status_code=400, detail=f"不支持的设备类型: {device_type}")

            # 构建查询条件
            where_conditions = []
            # device_type 用于选择表名，而不是作为查询条件
            # if device_type:
            #     where_conditions.append(f"device_type = '{device_type}'")
            if device_group:
                where_conditions.append(f"device_group = '{device_group}'")
            
            where_clause = " AND " + " AND ".join(where_conditions) if where_conditions else ""
            
            # 查询每日在线率统计数据
            statistics_data = []
            current_date = start_dt
            
            while current_date <= end_dt:
                date_str = current_date.strftime("%Y-%m-%d")
                next_date = current_date + timedelta(days=1)
                next_date_str = next_date.strftime("%Y-%m-%d")
                
                # 查询当日设备状态统计 - 从日汇总表获取数据
                query = f"""
                SELECT 
                    COUNT(*) as total_devices,
                    SUM(online_minutes) as total_online_minutes,
                    SUM(welding_minutes) as total_welding_minutes,
                    SUM(alarm_minutes) as total_alarm_minutes,
                    AVG(welding_minutes) as avg_welding_time,
                    AVG(online_rate) as avg_online_rate
                FROM hlzg_db.{table_name} 
                WHERE ts >= '{date_str}T00:00:00.000+08:00' AND ts < '{next_date_str}T00:00:00.000+08:00' {where_clause}
                """
                logger.info(f"TDengine查询SQL ({date_str}): {query.strip()}")
                
                try:
                    result = await tdengine_connector.execute_sql(query)
                    logger.info(f"TDengine查询结果 ({date_str}): {result}")
                    
                    if result and len(result) > 0:
                        row = result[0]
                        total_devices = int(row[0]) if row[0] is not None else 0
                        total_online_minutes = float(row[1]) if row[1] is not None else 0.0
                        total_welding_minutes = float(row[2]) if row[2] is not None else 0.0
                        total_alarm_minutes = float(row[3]) if row[3] is not None else 0.0
                        avg_welding_time = float(row[4]) if row[4] is not None else 0.0
                        avg_online_rate = float(row[5]) if row[5] is not None else 0.0
                        
                        # 计算设备数量（基于时长数据推算）
                        # 假设一天有1440分钟，如果设备有在线时长，则认为是在线设备
                        online_devices = total_devices if total_online_minutes > 0 else 0
                        welding_devices = total_devices if total_welding_minutes > 0 else 0
                        fault_devices = total_devices if total_alarm_minutes > 0 else 0
                        
                        # 使用平均在线率或计算在线率
                        online_rate = round(avg_online_rate, 1) if avg_online_rate > 0 else 0.0
                        welding_rate = round((total_welding_minutes / (total_devices * 1440)) * 100, 1) if total_devices > 0 else 0.0
                        logger.info(f"计算指标 ({date_str}): 总设备数={total_devices}, 在线率={online_rate}, 焊接率={welding_rate}")
                        
                    else:
                        # 如果没有数据，使用默认值
                        total_devices = 0
                        online_devices = 0
                        welding_devices = 0
                        fault_devices = 0
                        avg_welding_time = 0.0
                        online_rate = 0.0
                        welding_rate = 0.0
                        
                except Exception as query_error:
                    logger.error(f"TDengine查询或数据处理失败 ({date_str}): {query_error}", exc_info=True)
                    # 查询失败时使用默认值
                    total_devices = 0
                    online_devices = 0
                    welding_devices = 0
                    fault_devices = 0
                    avg_welding_time = 0.0
                    online_rate = 0.0
                    welding_rate = 0.0
                
                daily_data = {
                    "date": int(current_date.timestamp() * 1000),  # 转换为毫秒时间戳
                    "onlineRate": online_rate,
                    "weldingRate": welding_rate,
                    "onlineDevices": online_devices,
                    "weldingDevices": welding_devices,
                    "totalDevices": total_devices,
                    "avgWeldingTime": round(avg_welding_time, 1),
                    "faultDevices": fault_devices,
                }
                
                statistics_data.append(daily_data)
                current_date += timedelta(days=1)
            
            logger.info(f"成功获取在线率统计数据，共 {len(statistics_data)} 天的数据。")
            return statistics_data
            
        except Exception as e:
            logger.error(f"获取在线率统计数据过程中发生未预期错误: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"message": "获取在线率统计数据失败", "error": str(e), "error_type": type(e).__name__},
            )
        finally:
            if tdengine_connector:
                await tdengine_connector.close()
                logger.info("TDengine连接已关闭。")


    async def get_weld_time_statistics(
        self,
        device_type: Optional[str] = None,
        device_group: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[dict]:
        """获取焊接时长统计数据
        
        从TDengine查询焊接时长统计数据
        
        Args:
            device_type: 设备类型代码
            device_group: 设备组
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            
        Returns:
            焊接时长统计数据列表，每个元素包含一天的数据
        """
        tdengine_connector = None
        try:
            from datetime import datetime, timedelta
            from app.settings.config import TDengineCredentials
            
            logger.info(f"获取焊接时长统计数据 - 设备类型: {device_type}, 设备组: {device_group}, 开始日期: {start_date}, 结束日期: {end_date}")
            
            # 解析日期范围
            if start_date and end_date:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            else:
                # 默认查询最近7天
                end_dt = datetime.now()
                start_dt = end_dt - timedelta(days=6)
            
            # 初始化TDengine连接
            tdengine_creds = TDengineCredentials()
            tdengine_connector = TDengineConnector(
                host=tdengine_creds.host,
                port=tdengine_creds.port,
                user=tdengine_creds.user,
                password=tdengine_creds.password,
                database=tdengine_creds.database,
            )
            
            # 构建查询条件
            where_conditions = []
            if device_type:
                where_conditions.append(f"device_type = '{device_type}'")
            if device_group:
                where_conditions.append(f"device_group = '{device_group}'")
            
            where_clause = " AND " + " AND ".join(where_conditions) if where_conditions else ""
            
            # 查询每日焊接时长统计数据
            statistics_data = []
            current_date = start_dt
            
            while current_date <= end_dt:
                date_str = current_date.strftime("%Y-%m-%d")
                
                # 查询当日焊接时长统计
                query = f"""
                SELECT 
                    COUNT(DISTINCT device_code) as active_devices,
                    SUM(CASE WHEN status = 'welding' AND welding_duration > 0 THEN welding_duration ELSE 0 END) as total_weld_time,
                    AVG(CASE WHEN status = 'welding' AND welding_duration > 0 THEN welding_duration ELSE NULL END) as avg_weld_time,
                    MAX(CASE WHEN status = 'welding' AND welding_duration > 0 THEN welding_duration ELSE 0 END) as max_weld_time,
                    MIN(CASE WHEN status = 'welding' AND welding_duration > 0 THEN welding_duration ELSE NULL END) as min_weld_time,
                    COUNT(CASE WHEN status = 'welding' THEN 1 ELSE NULL END) as weld_count
                FROM device_realtime_data 
                WHERE ts >= '{date_str} 00:00:00' AND ts < '{date_str} 23:59:59'{where_clause}
                """
                
                try:
                    result = await tdengine_connector.execute_query(query)
                    
                    if result and len(result) > 0:
                        row = result[0]
                        active_devices = int(row[0]) if row[0] is not None else 0
                        total_weld_time = float(row[1]) if row[1] is not None else 0.0
                        avg_weld_time = float(row[2]) if row[2] is not None else 0.0
                        max_weld_time = float(row[3]) if row[3] is not None else 0.0
                        min_weld_time = float(row[4]) if row[4] is not None else 0.0
                        weld_count = int(row[5]) if row[5] is not None else 0
                        
                        # 计算焊接效率（假设一天工作8小时）
                        working_hours = 8.0
                        welding_efficiency = round(total_weld_time / (active_devices * working_hours) * 100, 1) if active_devices > 0 else 0.0
                        
                    else:
                        # 如果没有数据，使用默认值
                        active_devices = 0
                        total_weld_time = 0.0
                        avg_weld_time = 0.0
                        max_weld_time = 0.0
                        min_weld_time = 0.0
                        weld_count = 0
                        welding_efficiency = 0.0
                        
                except Exception as query_error:
                    logger.warning(f"查询日期 {date_str} 的焊接时长数据失败: {str(query_error)}，使用默认值")
                    # 查询失败时使用默认值
                    active_devices = 0
                    total_weld_time = 0.0
                    avg_weld_time = 0.0
                    max_weld_time = 0.0
                    min_weld_time = 0.0
                    weld_count = 0
                    welding_efficiency = 0.0
                
                daily_data = {
                    "date": int(current_date.timestamp() * 1000),  # 转换为毫秒时间戳
                    "totalWeldTime": round(total_weld_time, 1),
                    "avgWeldTime": round(avg_weld_time, 1),
                    "weldingEfficiency": welding_efficiency,
                    "activeDevices": active_devices,
                    "maxWeldTime": round(max_weld_time, 1),
                    "minWeldTime": round(min_weld_time, 1),
                    "weldCount": weld_count,
                }
                
                statistics_data.append(daily_data)
                current_date += timedelta(days=1)
            
            logger.info(f"查询了 {len(statistics_data)} 天的焊接时长统计数据")
            return statistics_data
            
        except Exception as e:
            logger.error(f"获取焊接时长统计数据失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"message": "获取焊接时长统计数据失败", "error": str(e), "error_type": type(e).__name__},
            )
        finally:
            if tdengine_connector:
                await tdengine_connector.close()

    async def get_alarm_category_summary(
        self, 
        start_time: str, 
        end_time: str
    ) -> dict:
        """获取报警类型分布统计数据
        
        Args:
            start_time: 开始时间 (YYYY-MM-DD)
            end_time: 结束时间 (YYYY-MM-DD)
            
        Returns:
            包含各报警类型的记录数和持续时间统计
        """
        try:
            logger.info(f"开始获取报警类型分布统计数据，时间范围: {start_time} 到 {end_time}")
            
            from datetime import datetime
            
            async with get_db_connection() as conn:
                # 查询t_welding_alarm_his表，按alarm_message分组统计
                alarm_summary_sql = """
                    SELECT alarm_message, 
                           COUNT(*) AS record_count, 
                           SUM(alarm_duration_sec) AS record_time 
                    FROM public.t_welding_alarm_his 
                    WHERE alarm_time >= $1 AND alarm_time <= $2
                    GROUP BY alarm_message
                    ORDER BY record_count DESC
                """
                
                # 转换日期格式为datetime对象
                start_datetime = datetime.strptime(start_time, '%Y-%m-%d')
                end_datetime = datetime.strptime(end_time, '%Y-%m-%d')
                # 结束时间设置为当天的23:59:59
                end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
                
                result = await conn.fetch(alarm_summary_sql, start_datetime, end_datetime)
                
                # 处理查询结果
                alarm_categories = []
                total_records = 0
                total_duration = 0
                
                for row in result:
                    record_count = row['record_count'] or 0
                    record_time = row['record_time'] or 0
                    
                    alarm_categories.append({
                        "alarm_message": row['alarm_message'],
                        "record_count": record_count,
                        "record_time": record_time
                    })
                    
                    total_records += record_count
                    total_duration += record_time
                
                logger.info(f"查询到 {len(alarm_categories)} 种报警类型，总记录数: {total_records}，总持续时间: {total_duration}秒")
                
                return {
                    "alarm_categories": alarm_categories,
                    "total_records": total_records,
                    "total_duration": total_duration,
                    "start_time": start_time,
                    "end_time": end_time
                }
                
        except Exception as e:
            logger.error("获取报警类型分布统计数据失败", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="获取报警类型分布统计数据失败"
            )

    async def get_online_welding_rate_statistics(
        self, 
        start_time: str, 
        end_time: str
    ) -> dict:
        """获取在线率和焊接率统计数据
        
        Args:
            start_time: 开始时间 (YYYY-MM-DD)
            end_time: 结束时间 (YYYY-MM-DD)
            
        Returns:
            包含每日数据的字典，包括设备总数、焊接设备数、开机设备数、关机设备数、在线率、焊接率
        """
        try:
            logger.info(f"开始获取在线率和焊接率统计数据，时间范围: {start_time} 到 {end_time}")
            
            from datetime import datetime, timedelta
            
            async with get_db_connection() as conn:
                # 1. 查询设备总数（device_type=welding）
                total_devices_sql = """
                    SELECT COUNT(*) as total_devices
                    FROM t_device_info 
                    WHERE device_type = 'welding'
                """
                total_result = await conn.fetchrow(total_devices_sql)
                total_devices = total_result['total_devices'] if total_result else 0
                
                # 2. 生成日期范围内的每一天
                start_date = datetime.strptime(start_time, '%Y-%m-%d')
                end_date = datetime.strptime(end_time, '%Y-%m-%d')
                
                daily_data = []
                current_date = start_date
                
                while current_date <= end_date:
                    date_str = current_date.strftime('%Y-%m-%d')
                    
                    # 查询当天的焊接设备数（welding_duration_seconds > 0）
                    welding_devices_sql = """
                        SELECT COUNT(DISTINCT prod_code) as welding_devices
                        FROM t_welding_daily_report 
                        WHERE report_date = $1
                        AND welding_duration_seconds > 0
                    """
                    welding_result = await conn.fetchrow(welding_devices_sql, current_date.date())
                    welding_devices = welding_result['welding_devices'] if welding_result else 0
                    
                    # 查询当天的开机设备数（有日报记录的设备）
                    online_devices_sql = """
                        SELECT COUNT(DISTINCT prod_code) as online_devices
                        FROM t_welding_daily_report 
                        WHERE report_date = $1
                    """
                    online_result = await conn.fetchrow(online_devices_sql, current_date.date())
                    online_devices = online_result['online_devices'] if online_result else 0
                    
                    # 计算关机设备数
                    shutdown_devices = total_devices - online_devices
                    
                    # 计算在线率和焊接率
                    online_rate = round((online_devices / total_devices * 100), 1) if total_devices > 0 else 0.0
                    welding_rate = round((welding_devices / online_devices * 100), 1) if online_devices > 0 else 0.0
                    
                    daily_data.append({
                        "date": date_str,
                        "total_devices": total_devices,
                        "welding_devices": welding_devices,
                        "online_devices": online_devices,
                        "shutdown_devices": shutdown_devices,
                        "online_rate": online_rate,
                        "welding_rate": welding_rate
                    })
                    
                    logger.info(f"日期 {date_str} - 总设备数: {total_devices}, 焊接设备数: {welding_devices}, 开机设备数: {online_devices}, 在线率: {online_rate}%, 焊接率: {welding_rate}%")
                    
                    current_date += timedelta(days=1)
                
                # 计算整个时间段的平均值
                if daily_data:
                    avg_online_rate = round(sum(d['online_rate'] for d in daily_data) / len(daily_data), 1)
                    avg_welding_rate = round(sum(d['welding_rate'] for d in daily_data) / len(daily_data), 1)
                    total_welding_devices = sum(d['welding_devices'] for d in daily_data)
                    total_online_devices = sum(d['online_devices'] for d in daily_data)
                else:
                    avg_online_rate = 0.0
                    avg_welding_rate = 0.0
                    total_welding_devices = 0
                    total_online_devices = 0
                
                return {
                    "total_devices": total_devices,
                    "welding_devices": total_welding_devices,
                    "online_devices": total_online_devices,
                    "shutdown_devices": total_devices - total_online_devices,
                    "online_rate": avg_online_rate,
                    "welding_rate": avg_welding_rate,
                    "daily_data": daily_data
                }
                
        except Exception as e:
            logger.error("获取在线率和焊接率统计数据失败", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="获取在线率和焊接率统计数据失败"
            )

    async def get_alarm_record_top(
        self, 
        start_time: str, 
        end_time: str,
        top: int = 10
    ) -> dict:
        """获取报警时长Top排名统计数据
        
        Args:
            start_time: 开始时间 (YYYY-MM-DD)
            end_time: 结束时间 (YYYY-MM-DD)
            top: 返回Top数量，默认10
            
        Returns:
            包含设备编码、设备名称、报警时长的Top排名数据
        """
        try:
            logger.info(f"开始获取报警时长Top{top}排名统计数据，时间范围: {start_time} 到 {end_time}")
            
            from datetime import datetime
            
            async with get_db_connection() as conn:
                # 查询t_welding_alarm_his表，按设备分组统计报警时长
                alarm_top_sql = """
                    SELECT 
                        a.prod_code, 
                        d.device_name, 
                        SUM(a.alarm_duration_sec) AS record_time 
                    FROM 
                        public.t_welding_alarm_his a 
                    JOIN 
                        public.t_device_info d 
                        ON a.prod_code = d.device_code 
                    WHERE 
                        a.alarm_time >= $1 AND a.alarm_time <= $2
                    GROUP BY 
                        a.prod_code, d.device_name 
                    ORDER BY 
                        record_time DESC 
                    LIMIT $3
                """
                
                # 转换日期格式为datetime对象
                start_datetime = datetime.strptime(start_time, '%Y-%m-%d')
                end_datetime = datetime.strptime(end_time, '%Y-%m-%d')
                # 结束时间设置为当天的23:59:59
                end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
                
                result = await conn.fetch(alarm_top_sql, start_datetime, end_datetime, top)
                
                # 处理查询结果
                alarm_records = []
                total_alarm_time = 0
                
                for index, row in enumerate(result, 1):
                    record_time = row['record_time'] or 0
                    
                    alarm_records.append({
                        "rank": index,
                        "prod_code": row['prod_code'],
                        "device_name": row['device_name'],
                        "record_time": record_time
                    })
                    
                    total_alarm_time += record_time
                
                logger.info(f"查询到 {len(alarm_records)} 条报警记录，总报警时长: {total_alarm_time}秒")
                
                return {
                    "alarm_records": alarm_records,
                    "total_alarm_time": total_alarm_time,
                    "start_time": start_time,
                    "end_time": end_time,
                    "top": top
                }
                
        except Exception as e:
            logger.error("获取报警时长Top排名统计数据失败", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="获取报警时长Top排名统计数据失败"
            )


# 创建控制器实例
device_data_controller = DeviceDataController()
