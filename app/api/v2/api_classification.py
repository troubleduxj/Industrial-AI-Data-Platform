"""
API分类管理系统优化接口
提供API分类审计、重组和自动映射功能
"""
from typing import Dict, Any
from fastapi import APIRouter, Request, Depends

from app.models.admin import User
from app.core.dependency import DependAuth
from app.core.response_formatter_v2 import ResponseFormatterV2
from app.services.api_classification_sync_service import api_classification_sync_service

router = APIRouter()

@router.get("/audit", summary="审计API分类匹配情况", dependencies=[DependAuth])
async def audit_api_classification(
    request: Request,
    current_user: User = DependAuth
):
    """审计当前API分类与实际V2端点的匹配情况"""
    formatter = ResponseFormatterV2(request)
    
    try:
        audit_result = await api_classification_sync_service.audit_current_classification()
        
        return formatter.success(
            data=audit_result,
            message="API分类审计完成",
            resource_type="api_classification_audit"
        )
        
    except Exception as e:
        return formatter.internal_error(f"API分类审计失败: {str(e)}")

@router.post("/reorganize", summary="重新组织API分类结构", dependencies=[DependAuth])
async def reorganize_api_groups(
    request: Request,
    current_user: User = DependAuth
):
    """重新组织API分类结构，确保逻辑分组与系统管理模块对应"""
    formatter = ResponseFormatterV2(request)
    
    try:
        reorganize_result = await api_classification_sync_service.reorganize_api_groups()
        
        return formatter.success(
            data=reorganize_result,
            message=f"API分类重组完成：创建 {len(reorganize_result['created_groups'])} 个，更新 {len(reorganize_result['updated_groups'])} 个分组",
            resource_type="api_groups_reorganization"
        )
        
    except Exception as e:
        return formatter.internal_error(f"重新组织API分类失败: {str(e)}")

@router.post("/auto-map", summary="自动映射API到分组", dependencies=[DependAuth])
async def auto_map_endpoints_to_groups(
    request: Request,
    current_user: User = DependAuth
):
    """实现API到分类的自动映射和同步机制"""
    formatter = ResponseFormatterV2(request)
    
    try:
        mapping_result = await api_classification_sync_service.auto_map_endpoints_to_groups()
        
        return formatter.success(
            data=mapping_result,
            message=f"自动映射完成：成功率 {mapping_result['success_rate']}，处理 {mapping_result['total_processed']} 个端点",
            resource_type="api_endpoint_mapping"
        )
        
    except Exception as e:
        return formatter.internal_error(f"自动映射API端点失败: {str(e)}")

@router.post("/sync-endpoints", summary="同步V2端点", dependencies=[DependAuth])
async def sync_v2_endpoints(
    request: Request,
    current_user: User = DependAuth
):
    """从FastAPI应用同步V2端点到数据库"""
    formatter = ResponseFormatterV2(request)
    
    try:
        # 获取FastAPI应用实例
        app = request.app
        sync_result = await api_classification_sync_service.sync_v2_endpoints_from_fastapi_app(app)
        
        return formatter.success(
            data=sync_result,
            message=f"端点同步完成：发现 {sync_result['total_discovered']} 个，创建 {sync_result['total_created']} 个，更新 {sync_result['total_updated']} 个",
            resource_type="api_endpoint_sync"
        )
        
    except Exception as e:
        return formatter.internal_error(f"同步V2端点失败: {str(e)}")

@router.get("/report", summary="生成分类管理报告", dependencies=[DependAuth])
async def generate_classification_report(
    request: Request,
    current_user: User = DependAuth
):
    """生成API分类管理报告"""
    formatter = ResponseFormatterV2(request)
    
    try:
        report = await api_classification_sync_service.generate_classification_report()
        
        return formatter.success(
            data=report,
            message="API分类管理报告生成完成",
            resource_type="api_classification_report"
        )
        
    except Exception as e:
        return formatter.internal_error(f"生成分类报告失败: {str(e)}")

@router.post("/optimize", summary="一键优化API分类系统", dependencies=[DependAuth])
async def optimize_api_classification_system(
    request: Request,
    current_user: User = DependAuth
):
    """一键执行完整的API分类系统优化流程"""
    formatter = ResponseFormatterV2(request)
    
    try:
        optimization_result = {
            'steps_completed': [],
            'steps_failed': [],
            'overall_success': True,
            'summary': {}
        }
        
        # 步骤1: 审计当前分类
        try:
            audit_result = await api_classification_sync_service.audit_current_classification()
            optimization_result['steps_completed'].append({
                'step': 'audit',
                'name': '审计API分类',
                'result': audit_result
            })
        except Exception as e:
            optimization_result['steps_failed'].append({
                'step': 'audit',
                'name': '审计API分类',
                'error': str(e)
            })
            optimization_result['overall_success'] = False
        
        # 步骤2: 重新组织分类结构
        if optimization_result['overall_success']:
            try:
                reorganize_result = await api_classification_sync_service.reorganize_api_groups()
                optimization_result['steps_completed'].append({
                    'step': 'reorganize',
                    'name': '重新组织分类结构',
                    'result': reorganize_result
                })
            except Exception as e:
                optimization_result['steps_failed'].append({
                    'step': 'reorganize',
                    'name': '重新组织分类结构',
                    'error': str(e)
                })
                optimization_result['overall_success'] = False
        
        # 步骤3: 自动映射端点
        if optimization_result['overall_success']:
            try:
                mapping_result = await api_classification_sync_service.auto_map_endpoints_to_groups()
                optimization_result['steps_completed'].append({
                    'step': 'auto_map',
                    'name': '自动映射端点到分组',
                    'result': mapping_result
                })
            except Exception as e:
                optimization_result['steps_failed'].append({
                    'step': 'auto_map',
                    'name': '自动映射端点到分组',
                    'error': str(e)
                })
                optimization_result['overall_success'] = False
        
        # 步骤4: 生成最终报告
        try:
            final_report = await api_classification_sync_service.generate_classification_report()
            optimization_result['steps_completed'].append({
                'step': 'report',
                'name': '生成优化报告',
                'result': final_report
            })
            optimization_result['summary'] = final_report['summary']
        except Exception as e:
            optimization_result['steps_failed'].append({
                'step': 'report',
                'name': '生成优化报告',
                'error': str(e)
            })
        
        # 生成总结消息
        completed_count = len(optimization_result['steps_completed'])
        failed_count = len(optimization_result['steps_failed'])
        
        if optimization_result['overall_success']:
            message = f"API分类系统优化完成：成功执行 {completed_count} 个步骤"
        else:
            message = f"API分类系统优化部分完成：成功 {completed_count} 个步骤，失败 {failed_count} 个步骤"
        
        return formatter.success(
            data=optimization_result,
            message=message,
            resource_type="api_classification_optimization"
        )
        
    except Exception as e:
        return formatter.internal_error(f"API分类系统优化失败: {str(e)}")