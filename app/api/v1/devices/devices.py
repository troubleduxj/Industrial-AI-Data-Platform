import logging
from typing import List, Optional

from fastapi import APIRouter, Body, Query, HTTPException
from tortoise.expressions import Q

from app.controllers.device import device_controller
from app.core.dependency import DependAuth
from app.schemas.base import Fail, Success, SuccessExtra
from app.schemas.devices import *

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/list", summary="查看设备列表", dependencies=[DependAuth])
async def list_devices(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    device_code: str = Query(None, description="设备编号，用于搜索"),
    device_name: str = Query(None, description="设备名称，用于搜索"),
    device_type: str = Query(None, description="设备类型"),
    manufacturer: str = Query(None, description="制造商"),
    install_location: str = Query(None, description="安装位置"),
    team_name: str = Query(None, description="班组名称"),
    is_locked: Optional[bool] = Query(None, description="是否锁定"),
    device_model: str = Query(None, description="设备型号"),
    online_address: str = Query(None, description="在线地址"),
):
    """获取设备列表，支持多条件查询和分页"""
    q = Q()
    if device_code:
        q &= Q(device_code__contains=device_code)
    if device_name:
        q &= Q(device_name__contains=device_name)
    if device_type:
        q &= Q(device_type__contains=device_type)
    if manufacturer:
        q &= Q(manufacturer__contains=manufacturer)
    if install_location:
        q &= Q(install_location__contains=install_location)
    if team_name:
        q &= Q(team_name__contains=team_name)
    if is_locked is not None:
        q &= Q(is_locked=is_locked)
    if device_model:
        q &= Q(device_model__contains=device_model)
    if online_address:
        q &= Q(online_address__contains=online_address)

    total, device_objs = await device_controller.get_multi_with_total(page=page, page_size=page_size, search=q)
    data = [await obj.to_dict() for obj in device_objs]

    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/get", summary="查看设备详情", dependencies=[DependAuth])
async def get_device(
    device_id: int = Query(..., description="设备ID"),
):
    """根据设备ID获取设备详细信息"""
    device_obj = await device_controller.get(id=device_id)
    if not device_obj:
        raise HTTPException(status_code=404, detail="设备不存在")

    device_dict = await device_obj.to_dict()
    return Success(data=device_dict)


@router.get("/get_by_code", summary="根据设备编号查看设备", dependencies=[DependAuth])
async def get_device_by_code(
    device_code: str = Query(..., description="设备编号"),
):
    """根据设备编号获取设备信息"""
    try:
        device_obj = await device_controller.get_by_device_code(device_code=device_code)
        if device_obj is None:
            raise HTTPException(status_code=404, detail="设备不存在")

        # 确保设备对象存在后再调用to_dict
        try:
            device_dict = await device_obj.to_dict(exclude_fields=["created_at", "updated_at"])
            return Success(data=device_dict)
        except Exception as e:
            logger.error(f"转换设备数据失败: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="转换设备数据失败")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取设备信息失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取设备信息失败")


@router.post("/create", summary="创建设备", dependencies=[DependAuth])
async def create_device(
    device_in: DeviceCreate,
):
    """创建新设备"""
    try:
        print(f"创建设备请求数据: {device_in.dict()}")
        device_obj = await device_controller.create_device(obj_in=device_in)
        return Success(data={"id": device_obj.id}, msg="设备创建成功")
    except ValueError as e:
        logger.error(f"创建设备参数错误: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建设备失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail={"message": "创建设备失败", "error": str(e), "error_type": type(e).__name__}
        )


@router.post("/update", summary="更新设备", dependencies=[DependAuth])
async def update_device(device_data: dict = Body(..., description="设备更新数据，包含id和更新字段")):
    """更新设备信息"""
    try:
        device_id = device_data.pop("id")
        device_in = DeviceUpdate(**device_data)
        await device_controller.update_device(id=device_id, obj_in=device_in)
        return Success(msg="设备更新成功")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新设备失败: {e}")
        raise HTTPException(status_code=500, detail="更新设备失败")


@router.delete("/delete", summary="删除设备", dependencies=[DependAuth])
async def delete_device(
    device_id: int = Query(..., description="设备ID"),
):
    """删除设备"""
    try:
        device_obj = await device_controller.get(id=device_id)
        if not device_obj:
            raise HTTPException(status_code=404, detail="设备不存在")

        await device_controller.delete_device(id=device_id)
        return Success(msg="设备删除成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除设备失败: {e}")
        raise HTTPException(status_code=500, detail="删除设备失败")


@router.get("/by_type", summary="按设备类型查询设备", dependencies=[DependAuth])
async def get_devices_by_type(
    device_type: str = Query(..., description="设备类型"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
):
    """按设备类型查询设备列表"""
    total, device_objs = await device_controller.get_devices_by_type(
        device_type=device_type, page=page, page_size=page_size
    )
    data = [await obj.to_dict() for obj in device_objs]

    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/by_location", summary="按安装位置查询设备", dependencies=[DependAuth])
async def get_devices_by_location(
    install_location: str = Query(..., description="安装位置"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
):
    """按安装位置查询设备列表"""
    total, device_objs = await device_controller.get_devices_by_location(
        install_location=install_location, page=page, page_size=page_size
    )
    data = [await obj.to_dict() for obj in device_objs]

    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/by_team", summary="按班组查询设备", dependencies=[DependAuth])
async def get_devices_by_team(
    team_name: str = Query(..., description="班组名称"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
):
    """按班组查询设备列表"""
    total, device_objs = await device_controller.get_devices_by_team(
        team_name=team_name, page=page, page_size=page_size
    )
    data = [await obj.to_dict() for obj in device_objs]

    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/locked", summary="查询锁定设备", dependencies=[DependAuth])
async def get_locked_devices(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
):
    """查询所有锁定的设备"""
    total, device_objs = await device_controller.get_locked_devices(page=page, page_size=page_size)
    data = [await obj.to_dict() for obj in device_objs]

    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.post("/toggle_lock", summary="切换设备锁定状态", dependencies=[DependAuth])
async def toggle_device_lock(
    id: int = Body(..., description="设备ID"),
):
    """切换设备的锁定状态"""
    try:
        device_obj = await device_controller.toggle_device_lock(id=id)
        status = "锁定" if device_obj.is_locked else "解锁"
        return Success(data={"is_locked": device_obj.is_locked}, msg=f"设备{status}成功")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"切换设备锁定状态失败: {e}")
        raise HTTPException(status_code=500, detail="操作失败")


@router.get("/search", summary="多条件搜索设备", dependencies=[DependAuth])
async def search_devices(
    keyword: str = Query("", description="关键词，搜索设备编号、名称、型号"),
    device_type: str = Query("", description="设备类型"),
    manufacturer: str = Query("", description="制造商"),
    install_location: str = Query("", description="安装位置"),
    team_name: str = Query("", description="班组名称"),
    is_locked: Optional[bool] = Query(None, description="是否锁定"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
):
    """多条件搜索设备"""
    total, device_objs = await device_controller.search_devices(
        keyword=keyword,
        device_type=device_type,
        manufacturer=manufacturer,
        team_name=team_name,
        is_locked=is_locked,
        page=page,
        page_size=page_size,
    )
    data = [await obj.to_dict() for obj in device_objs]

    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/statistics", summary="设备统计信息", dependencies=[DependAuth])
async def get_device_statistics():
    """获取设备统计信息"""
    try:
        # 总设备数
        total_devices = await device_controller.count()

        # 锁定设备数
        locked_count = await device_controller.count(search=Q(is_locked=True))
        unlocked_count = total_devices - locked_count

        # 按类型统计
        type_stats = await device_controller.get_type_statistics()

        # 按班组统计
        team_stats = await device_controller.get_team_statistics()

        statistics = {
            "total_devices": total_devices,
            "locked_devices": locked_count,
            "unlocked_devices": unlocked_count,
            "device_types": type_stats,
            "teams": team_stats,
        }

        return Success(data=statistics)
    except Exception as e:
        logger.error(f"获取设备统计信息失败: {e}")
        raise HTTPException(status_code=500, detail="获取统计信息失败")


@router.post("/batch_import", summary="批量导入设备(支持更新模式)", dependencies=[DependAuth])
async def batch_import_devices(
    devices: List[DeviceCreate],
    update_existing: bool = Body(
        False, description="是否更新已存在的设备: \n" "- False(默认): 跳过已存在设备\n" "- True: 更新已存在设备"
    ),
):
    """批量导入设备信息

    Args:
        devices (List[DeviceCreate]): 要导入的设备列表
        update_existing (bool): 处理已存在设备的模式
            - False(默认): 跳过已存在设备，记录为失败项
            - True: 更新已存在设备的数据

    Returns:
        Success: 包含导入结果的响应
            - total_count: 总设备数
            - success_count: 成功数量
            - failed_count: 失败数量
            - failed_items: 失败详情列表
    """
    try:
        success_count = 0
        failed_items = []

        for i, device_data in enumerate(devices):
            try:
                # 检查设备编号是否已存在
                existing_device = await device_controller.get_by_device_code(device_code=device_data.device_code)
                if existing_device:
                    if update_existing:
                        # 更新现有设备
                        await device_controller.update_device(
                            id=existing_device.id, obj_in=DeviceUpdate(**device_data.dict())
                        )
                        success_count += 1
                        logger.info(f"成功更新设备: {existing_device.id} - {existing_device.device_code}")
                    else:
                        failed_items.append(
                            {"index": i + 1, "device_code": device_data.device_code, "error": "设备编号已存在"}
                        )
                    continue

                # 创建设备
                device_obj = await device_controller.create_device(obj_in=device_data)
                success_count += 1
                logger.info(f"成功导入设备: {device_obj.id} - {device_obj.device_code}")

            except HTTPException as e:
                failed_items.append(
                    {
                        "index": i + 1,
                        "device_code": device_data.device_code,
                        "error": e.detail.get("message", str(e.detail)),
                    }
                )
            except Exception as e:
                logger.error(f"导入设备失败: {str(e)}", exc_info=True)
                failed_items.append(
                    {
                        "index": i + 1,
                        "device_code": device_data.device_code,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                )

        result = {
            "total_count": len(devices),
            "success_count": success_count,
            "failed_count": len(failed_items),
            "failed_items": failed_items,
        }

        if failed_items:
            logger.warning(f"批量导入完成，成功{success_count}条，失败{len(failed_items)}条")
        else:
            logger.info(f"批量导入完成，全部{success_count}条成功")

        return Success(data=result, msg=f"批量导入完成，成功{success_count}条，失败{len(failed_items)}条")

    except Exception as e:
        logger.error(f"批量导入设备失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail={"message": "批量导入失败", "error": str(e), "error_type": type(e).__name__}
        )
