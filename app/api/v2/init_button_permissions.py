"""
按钮权限初始化API
仅供超级管理员使用
"""

from fastapi import APIRouter, Depends, Request
from app.core.dependency import DependAuth
from app.core.response_formatter_v2 import ResponseFormatterV2
from app.models.admin import Menu, User
from app.log import logger


router = APIRouter(tags=["系统初始化"])


# 按钮权限配置
BUTTON_PERMISSIONS = [
    # 用户管理页面的按钮权限
    {
        "parent_menu_name": "用户管理",
        "buttons": [
            {"name": "新建用户", "perms": "POST /api/v2/users", "icon": "material-symbols:add", "order": 1},
            {"name": "编辑用户", "perms": "PUT /api/v2/users/{id}", "icon": "material-symbols:edit", "order": 2},
            {"name": "删除用户", "perms": "DELETE /api/v2/users/{id}", "icon": "material-symbols:delete", "order": 3},
            {"name": "重置密码", "perms": "POST /api/v2/users/{id}/actions/reset-password", "icon": "material-symbols:lock-reset", "order": 4},
            {"name": "批量删除用户", "perms": "DELETE /api/v2/users/batch", "icon": "material-symbols:delete-sweep", "order": 5},
            {"name": "导出用户", "perms": "GET /api/v2/users/export", "icon": "material-symbols:download", "order": 6}
        ]
    },
    # 角色管理页面的按钮权限
    {
        "parent_menu_name": "角色管理",
        "buttons": [
            {"name": "新建角色", "perms": "POST /api/v2/roles", "icon": "material-symbols:add", "order": 1},
            {"name": "编辑角色", "perms": "PUT /api/v2/roles/{id}", "icon": "material-symbols:edit", "order": 2},
            {"name": "删除角色", "perms": "DELETE /api/v2/roles/{id}", "icon": "material-symbols:delete", "order": 3},
            {"name": "分配权限", "perms": "POST /api/v2/roles/{id}/permissions", "icon": "material-symbols:key", "order": 4}
        ]
    },
    # 菜单管理页面的按钮权限
    {
        "parent_menu_name": "菜单管理",
        "buttons": [
            {"name": "新建菜单", "perms": "POST /api/v2/menus", "icon": "material-symbols:add", "order": 1},
            {"name": "编辑菜单", "perms": "PUT /api/v2/menus/{id}", "icon": "material-symbols:edit", "order": 2},
            {"name": "删除菜单", "perms": "DELETE /api/v2/menus/{id}", "icon": "material-symbols:delete", "order": 3}
        ]
    },
    # 部门管理页面的按钮权限
    {
        "parent_menu_name": "部门管理",
        "buttons": [
            {"name": "新建部门", "perms": "POST /api/v2/departments", "icon": "material-symbols:add", "order": 1},
            {"name": "编辑部门", "perms": "PUT /api/v2/departments/{id}", "icon": "material-symbols:edit", "order": 2},
            {"name": "删除部门", "perms": "DELETE /api/v2/departments/{id}", "icon": "material-symbols:delete", "order": 3}
        ]
    },
    # 设备管理页面的按钮权限
    {
        "parent_menu_name": "设备信息管理",  # 修改为实际的菜单名称
        "buttons": [
            {"name": "新建设备", "perms": "POST /api/v2/devices", "icon": "material-symbols:add", "order": 1},
            {"name": "编辑设备", "perms": "PUT /api/v2/devices/{id}", "icon": "material-symbols:edit", "order": 2},
            {"name": "删除设备", "perms": "DELETE /api/v2/devices/{id}", "icon": "material-symbols:delete", "order": 3},
            {"name": "导出设备", "perms": "GET /api/v2/devices/export", "icon": "material-symbols:download", "order": 4}
        ]
    },
    # 设备分类管理页面的按钮权限
    {
        "parent_menu_name": "设备分类管理",
        "buttons": [
            {"name": "新建设备类型", "perms": "POST /api/v2/devices/types", "icon": "material-symbols:add", "order": 1},
            {"name": "编辑设备类型", "perms": "PUT /api/v2/devices/types/{id}", "icon": "material-symbols:edit", "order": 2},
            {"name": "删除设备类型", "perms": "DELETE /api/v2/devices/types/{id}", "icon": "material-symbols:delete", "order": 3}
        ]
    },
    # 维修记录页面的按钮权限
    {
        "parent_menu_name": "维修记录",
        "buttons": [
            {"name": "新建维修记录", "perms": "POST /api/v2/device/maintenance/repair-records", "icon": "material-symbols:add", "order": 1},
            {"name": "编辑维修记录", "perms": "PUT /api/v2/device/maintenance/repair-records/{id}", "icon": "material-symbols:edit", "order": 2},
            {"name": "删除维修记录", "perms": "DELETE /api/v2/device/maintenance/repair-records/{id}", "icon": "material-symbols:delete", "order": 3},
            {"name": "导出维修记录", "perms": "GET /api/v2/device/maintenance/repair-records/export", "icon": "material-symbols:download", "order": 4}
        ]
    },
    # 字典类型管理页面的按钮权限
    {
        "parent_menu_name": "字典类型",
        "buttons": [
            {"name": "新建字典类型", "perms": "POST /api/v2/dict-types", "icon": "material-symbols:add", "order": 1},
            {"name": "编辑字典类型", "perms": "PUT /api/v2/dict-types/{id}", "icon": "material-symbols:edit", "order": 2},
            {"name": "删除字典类型", "perms": "DELETE /api/v2/dict-types/{id}", "icon": "material-symbols:delete", "order": 3}
        ]
    },
    # 字典数据管理页面的按钮权限
    {
        "parent_menu_name": "字典数据",
        "buttons": [
            {"name": "新建字典数据", "perms": "POST /api/v2/dict-data", "icon": "material-symbols:add", "order": 1},
            {"name": "编辑字典数据", "perms": "PUT /api/v2/dict-data/{id}", "icon": "material-symbols:edit", "order": 2},
            {"name": "删除字典数据", "perms": "DELETE /api/v2/dict-data/{id}", "icon": "material-symbols:delete", "order": 3}
        ]
    },
    # 焊接记录页面的按钮权限
    {
        "parent_menu_name": "焊机-焊接记录",  # 修正菜单名称
        "buttons": [
            {"name": "导出焊接记录", "perms": "GET /api/v2/statistics/weld-records/export", "icon": "material-symbols:download", "order": 1}
        ]
    },
    # 焊接时长页面的按钮权限
    {
        "parent_menu_name": "焊机-焊接时长",  # 修正菜单名称
        "buttons": [
            {"name": "导出焊接时长", "perms": "GET /api/v2/statistics/weld-time/export", "icon": "material-symbols:download", "order": 1}
        ]
    },
    # 在线率统计页面的按钮权限
    {
        "parent_menu_name": "焊机-在线率",  # 修正菜单名称
        "buttons": [
            {"name": "导出在线率", "perms": "GET /api/v2/statistics/online-rate/export", "icon": "material-symbols:download", "order": 1}
        ]
    },
    # 审计日志页面的按钮权限
    {
        "parent_menu_name": "审计日志",
        "buttons": [
            {"name": "导出日志", "perms": "GET /api/v2/audit-logs/export", "icon": "material-symbols:download", "order": 1}
        ]
    },
    # API分组管理页面的按钮权限
    {
        "parent_menu_name": "API分组管理",  # 修正菜单名称
        "buttons": [
            {"name": "新建API分组", "perms": "POST /api/v2/api-groups", "icon": "material-symbols:add", "order": 1},
            {"name": "编辑API分组", "perms": "PUT /api/v2/api-groups/{id}", "icon": "material-symbols:edit", "order": 2},
            {"name": "删除API分组", "perms": "DELETE /api/v2/api-groups/{id}", "icon": "material-symbols:delete", "order": 3}
        ]
    },
    # 工作流管理页面的按钮权限
    {
        "parent_menu_name": "工作流管理",
        "buttons": [
            {"name": "新建工作流", "perms": "POST /api/v2/workflows", "icon": "material-symbols:add", "order": 1},
            {"name": "编辑工作流", "perms": "PUT /api/v2/workflows/{id}", "icon": "material-symbols:edit", "order": 2},
            {"name": "删除工作流", "perms": "DELETE /api/v2/workflows/{id}", "icon": "material-symbols:delete", "order": 3},
            {"name": "发布工作流", "perms": "POST /api/v2/workflows/{id}/publish", "icon": "material-symbols:publish", "order": 4}
        ]
    },
    # 工作流设计页面的按钮权限
    {
        "parent_menu_name": "工作流设计",
        "buttons": [
            {"name": "保存工作流", "perms": "POST /api/v2/workflows/save", "icon": "material-symbols:save", "order": 1},
            {"name": "发布工作流", "perms": "POST /api/v2/workflows/publish", "icon": "material-symbols:publish", "order": 2},
            {"name": "导出工作流", "perms": "GET /api/v2/workflows/export", "icon": "material-symbols:download", "order": 3}
        ]
    },
    # 历史数据查询页面的按钮权限
    {
        "parent_menu_name": "历史数据查询",  # 修正菜单名称
        "buttons": [
            {"name": "导出历史数据", "perms": "GET /api/v2/device-monitor/history/export", "icon": "material-symbols:download", "order": 1}
        ]
    },
    # 报警分析页面的按钮权限
    {
        "parent_menu_name": "报警分析",
        "buttons": [
            {"name": "导出报警分析", "perms": "GET /api/v2/alarms/analysis/export", "icon": "material-symbols:download", "order": 1}
        ]
    },
    # 异常检测页面的按钮权限
    {
        "parent_menu_name": "异常检测",
        "buttons": [
            {"name": "处理异常", "perms": "POST /api/v2/ai-monitor/anomalies/{id}/handle", "icon": "material-symbols:check-circle", "order": 1},
            {"name": "导出异常记录", "perms": "GET /api/v2/ai-monitor/anomalies/export", "icon": "material-symbols:download", "order": 2}
        ]
    },
    # Mock数据管理页面的按钮权限
    {
        "parent_menu_name": "Mock数据管理",
        "buttons": [
            {"name": "新建Mock规则", "perms": "POST /api/v2/mock-data", "icon": "material-symbols:add", "order": 1},
            {"name": "编辑Mock规则", "perms": "PUT /api/v2/mock-data/{id}", "icon": "material-symbols:edit", "order": 2},
            {"name": "删除Mock规则", "perms": "DELETE /api/v2/mock-data/{id}", "icon": "material-symbols:delete", "order": 3},
            {"name": "批量删除Mock", "perms": "POST /api/v2/mock-data/batch-delete", "icon": "material-symbols:delete-sweep", "order": 4},
            {"name": "切换Mock状态", "perms": "POST /api/v2/mock-data/{id}/toggle", "icon": "material-symbols:toggle-on", "order": 5}
        ]
    }
]


@router.post("/system/init-button-permissions", summary="初始化按钮权限", dependencies=[DependAuth])
async def init_button_permissions(request: Request, current_user=DependAuth):
    """
    初始化按钮权限数据
    仅供超级管理员使用
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查是否为超级管理员
        user_obj = await User.get(id=current_user.id)
        if not user_obj.is_superuser:
            return formatter.forbidden("只有超级管理员可以执行此操作")
        
        total_created = 0
        total_skipped = 0
        details = []
        
        for config in BUTTON_PERMISSIONS:
            parent_menu_name = config["parent_menu_name"]
            buttons = config["buttons"]
            
            # 查找父菜单
            parent_menu = await Menu.filter(name=parent_menu_name, menu_type="menu").first()
            
            if not parent_menu:
                logger.warning(f"未找到父菜单: {parent_menu_name}")
                details.append({
                    "menu": parent_menu_name,
                    "status": "skipped",
                    "reason": "父菜单不存在"
                })
                total_skipped += len(buttons)
                continue
            
            menu_details = {
                "menu": parent_menu_name,
                "buttons": []
            }
            
            for button in buttons:
                button_name = button["name"]
                perms = button["perms"]
                
                # 检查按钮权限是否已存在
                existing = await Menu.filter(
                    name=button_name,
                    parent_id=parent_menu.id,
                    menu_type="button"
                ).first()
                
                if existing:
                    menu_details["buttons"].append({
                        "name": button_name,
                        "status": "existed"
                    })
                    total_skipped += 1
                    continue
                
                # 创建按钮权限
                await Menu.create(
                    name=button_name,
                    path="",
                    component="",
                    menu_type="button",
                    icon=button.get("icon", ""),
                    order_num=button.get("order", 0),
                    parent_id=parent_menu.id,
                    perms=perms,
                    visible=True,
                    status=True,
                    is_frame=False,
                    is_cache=False
                )
                
                menu_details["buttons"].append({
                    "name": button_name,
                    "perms": perms,
                    "status": "created"
                })
                total_created += 1
            
            details.append(menu_details)
        
        # 查询当前总数
        total_button_count = await Menu.filter(menu_type="button").count()
        
        return formatter.success(
            data={
                "created": total_created,
                "skipped": total_skipped,
                "total_buttons": total_button_count,
                "details": details
            },
            message=f"按钮权限初始化完成！新创建: {total_created}个，已跳过: {total_skipped}个",
            code=200
        )
        
    except Exception as e:
        logger.error(f"初始化按钮权限失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"初始化失败: {str(e)}")

