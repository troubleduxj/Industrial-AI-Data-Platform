from datetime import date
from typing import List, Optional
from app.core.database import get_db_connection
from app.schemas.welding_daily_report import (
    WeldingDailyReportQuery,
    WeldingDailyReportSummary,
    WeldingDailyReportDetail,
    WeldingDailyReportDetailList
)
from app.core.unified_logger import get_logger

logger = get_logger(__name__)


class WeldingDailyReportController:
    """焊机日报控制器"""
    
    async def get_daily_report_summary(self, report_date: date, prod_code: Optional[str] = None) -> WeldingDailyReportSummary:
        """
        获取焊机日报汇总数据
        
        Args:
            report_date: 报告日期
            prod_code: 设备编码（可选）
            
        Returns:
            WeldingDailyReportSummary: 汇总数据
        """
        try:
            async with get_db_connection() as conn:
                # 构建SQL查询
                sql = """
                    SELECT 
                        SUM(welding_duration_seconds) AS total_duration,
                        SUM(wire_consumption_kg) AS total_wire,
                        SUM(gas_consumption_l) AS total_gas,
                        SUM(energy_consumption_kwh) AS total_energy
                    FROM t_welding_daily_report 
                    WHERE report_date = $1
                """
                
                params = [report_date]
                
                # 如果提供了设备编码，添加筛选条件
                if prod_code:
                    sql += " AND prod_code = $2"
                    params.append(prod_code)
                
                # 执行查询
                result = await conn.fetchrow(sql, *params)
                
                if result:
                    return WeldingDailyReportSummary(
                        total_duration=result['total_duration'] or 0,
                        total_wire=result['total_wire'] or 0.0,
                        total_gas=result['total_gas'] or 0.0,
                        total_energy=result['total_energy'] or 0.0
                    )
                else:
                    # 如果没有数据，返回空值
                    return WeldingDailyReportSummary(
                        total_duration=0,
                        total_wire=0.0,
                        total_gas=0.0,
                        total_energy=0.0
                    )
                    
        except Exception as e:
            logger.error(f"获取焊机日报汇总数据失败: {str(e)}")
            raise Exception(f"获取焊机日报汇总数据失败: {str(e)}")
    
    async def get_daily_report_detail(self, report_date: date, page: int = 1, page_size: int = 10, prod_code: Optional[str] = None) -> WeldingDailyReportDetailList:
        """
        获取焊机日报详情数据
        
        Args:
            report_date: 报告日期
            page: 页码，从1开始
            page_size: 每页记录数
            prod_code: 设备编码（可选）
            
        Returns:
            WeldingDailyReportDetailList: 详情数据列表
        """
        try:
            async with get_db_connection() as conn:
                # 先获取总记录数
                count_sql = """
                    SELECT COUNT(*) as total
                    FROM t_welding_daily_report 
                    WHERE report_date = $1
                """
                
                count_params = [report_date]
                
                # 如果提供了设备编码，添加筛选条件
                if prod_code:
                    count_sql += " AND prod_code = $2"
                    count_params.append(prod_code)
                
                total_result = await conn.fetchrow(count_sql, *count_params)
                total_count = total_result['total'] if total_result else 0
                
                # 计算偏移量
                offset = (page - 1) * page_size
                
                # 构建分页SQL查询
                sql = """
                    SELECT 
                        id,
                        prod_code,
                        report_date,
                        shift_name as shift,
                        team_name as operator,
                        welding_duration_seconds as welding_duration_sec,
                        wire_consumption_kg as wire_consumed_kg,
                        gas_consumption_l as gas_consumed_liter,
                        energy_consumption_kwh as energy_consumed_kwh,
                        NULL as weld_length_m,
                        NULL as defect_count,
                        NULL as rework_count,
                        NULL as quality_score,
                        NULL as notes,
                        created_at,
                        updated_at
                    FROM t_welding_daily_report 
                    WHERE report_date = $1
                """
                
                detail_params = [report_date]
                
                # 如果提供了设备编码，添加筛选条件
                if prod_code:
                    sql += " AND prod_code = $2"
                    detail_params.append(prod_code)
                    sql += " ORDER BY prod_code LIMIT $3 OFFSET $4"
                    detail_params.extend([page_size, offset])
                else:
                    sql += " ORDER BY prod_code LIMIT $2 OFFSET $3"
                    detail_params.extend([page_size, offset])
                
                # 执行查询
                results = await conn.fetch(sql, *detail_params)
                
                # 转换为响应模型
                detail_list = []
                for row in results:
                    detail = WeldingDailyReportDetail(
                        id=row['id'],
                        prod_code=row['prod_code'],
                        report_date=row['report_date'].isoformat() if row['report_date'] else None,
                        shift=row['shift'],
                        operator=row['operator'],
                        welding_duration_sec=row['welding_duration_sec'],
                        wire_consumed_kg=row['wire_consumed_kg'],
                        gas_consumed_liter=row['gas_consumed_liter'],
                        energy_consumed_kwh=row['energy_consumed_kwh'],
                        weld_length_m=row['weld_length_m'],
                        defect_count=row['defect_count'],
                        rework_count=row['rework_count'],
                        quality_score=row['quality_score'],
                        notes=row['notes'],
                        created_at=str(row['created_at']) if row['created_at'] else None,
                        updated_at=str(row['updated_at']) if row['updated_at'] else None
                    )
                    detail_list.append(detail)
                
                return WeldingDailyReportDetailList(
                    data=detail_list,
                    total=total_count
                )
                    
        except Exception as e:
            logger.error(f"获取焊机日报详情数据失败: {str(e)}")
            raise Exception(f"获取焊机日报详情数据失败: {str(e)}")
    
    async def get_daily_report_detail_all(self, report_date: date, prod_code: Optional[str] = None) -> WeldingDailyReportDetailList:
        """
        获取焊机日报所有详情数据（不分页）
        
        Args:
            report_date: 报告日期
            prod_code: 设备编码（可选）
            
        Returns:
            WeldingDailyReportDetailList: 详情数据列表
        """
        try:
            async with get_db_connection() as conn:
                # 先获取总记录数
                count_sql = """
                    SELECT COUNT(*) as total
                    FROM t_welding_daily_report 
                    WHERE report_date = $1
                """
                
                count_params = [report_date]
                
                # 如果提供了设备编码，添加筛选条件
                if prod_code:
                    count_sql += " AND prod_code = $2"
                    count_params.append(prod_code)
                
                total_result = await conn.fetchrow(count_sql, *count_params)
                total_count = total_result['total'] if total_result else 0
                
                # 构建SQL查询（不分页）
                sql = """
                    SELECT 
                        id,
                        prod_code,
                        report_date,
                        shift_name as shift,
                        team_name as operator,
                        welding_duration_seconds as welding_duration_sec,
                        wire_consumption_kg as wire_consumed_kg,
                        gas_consumption_l as gas_consumed_liter,
                        energy_consumption_kwh as energy_consumed_kwh,
                        NULL as weld_length_m,
                        NULL as defect_count,
                        NULL as rework_count,
                        NULL as quality_score,
                        NULL as notes,
                        created_at,
                        updated_at
                    FROM t_welding_daily_report 
                    WHERE report_date = $1
                """
                
                detail_params = [report_date]
                
                # 如果提供了设备编码，添加筛选条件
                if prod_code:
                    sql += " AND prod_code = $2"
                    detail_params.append(prod_code)
                
                sql += " ORDER BY prod_code"
                
                # 执行查询
                results = await conn.fetch(sql, *detail_params)
                
                # 转换为响应模型
                detail_list = []
                for row in results:
                    detail = WeldingDailyReportDetail(
                        id=row['id'],
                        prod_code=row['prod_code'],
                        report_date=row['report_date'].isoformat() if row['report_date'] else None,
                        shift=row['shift'],
                        operator=row['operator'],
                        welding_duration_sec=row['welding_duration_sec'],
                        wire_consumed_kg=row['wire_consumed_kg'],
                        gas_consumed_liter=row['gas_consumed_liter'],
                        energy_consumed_kwh=row['energy_consumed_kwh'],
                        weld_length_m=row['weld_length_m'],
                        defect_count=row['defect_count'],
                        rework_count=row['rework_count'],
                        quality_score=row['quality_score'],
                        notes=row['notes'],
                        created_at=str(row['created_at']) if row['created_at'] else None,
                        updated_at=str(row['updated_at']) if row['updated_at'] else None
                    )
                    detail_list.append(detail)
                
                return WeldingDailyReportDetailList(
                    data=detail_list,
                    total=total_count
                )
                    
        except Exception as e:
            logger.error(f"获取焊机日报所有详情数据失败: {str(e)}")
            raise Exception(f"获取焊机日报所有详情数据失败: {str(e)}")