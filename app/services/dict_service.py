from typing import Dict, List, Optional
import logging
from app.models.system import SysDictType, SysDictData

logger = logging.getLogger(__name__)


class DictService:
    """字典服务
    
    提供字典数据的查询和验证功能，支持采集器配置中的字典值验证。
    """
    
    def __init__(self):
        self._dict_cache = {}  # 字典缓存
    
    async def get_dict_values(self, dict_type_code: str) -> List[str]:
        """获取字典类型的所有有效值
        
        Args:
            dict_type_code: 字典类型代码
            
        Returns:
            List[str]: 字典值列表
        """
        try:
            # 检查缓存
            if dict_type_code in self._dict_cache:
                return self._dict_cache[dict_type_code]
            
            # 查询字典类型
            dict_type_obj = await SysDictType.filter(
                type_code=dict_type_code
            ).first()
            
            if not dict_type_obj:
                logger.warning(f"字典类型不存在: {dict_type_code}")
                return []
            
            # 查询字典数据
            dict_data_list = await SysDictData.filter(
                dict_type=dict_type_obj,
                is_enabled=True
            ).order_by("sort_order").all()
            
            # 提取字典值
            values = [item.data_value for item in dict_data_list]
            
            # 缓存结果
            self._dict_cache[dict_type_code] = values
            
            logger.debug(f"获取字典值成功 - 类型: {dict_type_code}, 数量: {len(values)}")
            
            return values
            
        except Exception as e:
            logger.error(f"获取字典值失败 - 类型: {dict_type_code}, 错误: {e}")
            return []
    
    async def get_dict_data_map(self, dict_type_code: str) -> Dict[str, Dict[str, str]]:
        """获取字典类型的完整数据映射
        
        Args:
            dict_type_code: 字典类型代码
            
        Returns:
            Dict[str, Dict[str, str]]: 字典数据映射 {dict_value: {label, remark, ...}}
        """
        try:
            # 查询字典类型
            dict_type_obj = await SysDictType.filter(
                type_code=dict_type_code
            ).first()
            
            if not dict_type_obj:
                logger.warning(f"字典类型不存在: {dict_type_code}")
                return {}
            
            # 查询字典数据
            dict_data_list = await SysDictData.filter(
                dict_type=dict_type_obj,
                is_enabled=True
            ).order_by("sort_order").all()
            
            # 构建数据映射
            data_map = {}
            for item in dict_data_list:
                data_map[item.data_value] = {
                    'label': item.data_label,
                    'remark': item.remark or '',
                    'sort': item.sort_order,
                    'css_class': item.css_class or '',
                    'list_class': item.list_class or ''
                }
            
            logger.debug(f"获取字典数据映射成功 - 类型: {dict_type_code}, 数量: {len(data_map)}")
            
            return data_map
            
        except Exception as e:
            logger.error(f"获取字典数据映射失败 - 类型: {dict_type_code}, 错误: {e}")
            return {}
    
    async def validate_dict_value(self, dict_type_code: str, value: str) -> bool:
        """验证字典值是否有效
        
        Args:
            dict_type_code: 字典类型代码
            value: 要验证的值
            
        Returns:
            bool: 是否有效
        """
        try:
            valid_values = await self.get_dict_values(dict_type_code)
            is_valid = value in valid_values
            
            if not is_valid:
                logger.warning(f"字典值验证失败 - 类型: {dict_type_code}, 值: {value}, 有效值: {valid_values}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"字典值验证异常 - 类型: {dict_type_code}, 值: {value}, 错误: {e}")
            return False
    
    async def get_dict_label(self, dict_type_code: str, value: str) -> Optional[str]:
        """根据字典值获取标签
        
        Args:
            dict_type_code: 字典类型代码
            value: 字典值
            
        Returns:
            Optional[str]: 字典标签，如果不存在返回None
        """
        try:
            # 查询字典类型
            dict_type_obj = await SysDictType.filter(
                type_code=dict_type_code
            ).first()
            
            if not dict_type_obj:
                logger.warning(f"字典类型不存在: {dict_type_code}")
                return None
            
            # 查询字典数据
            dict_data = await SysDictData.filter(
                dict_type=dict_type_obj,
                data_value=value,
                is_enabled=True
            ).first()
            
            if dict_data:
                return dict_data.data_label
            
            logger.warning(f"字典标签不存在 - 类型: {dict_type_code}, 值: {value}")
            return None
            
        except Exception as e:
            logger.error(f"获取字典标签失败 - 类型: {dict_type_code}, 值: {value}, 错误: {e}")
            return None
    
    def clear_cache(self, dict_type_code: str = None):
        """清除字典缓存
        
        Args:
            dict_type_code: 字典类型代码，如果为None则清除所有缓存
        """
        if dict_type_code:
            self._dict_cache.pop(dict_type_code, None)
            logger.debug(f"清除字典缓存 - 类型: {dict_type_code}")
        else:
            self._dict_cache.clear()
            logger.debug("清除所有字典缓存")
    
    async def get_all_dict_types(self) -> List[Dict[str, str]]:
        """获取所有字典类型
        
        Returns:
            List[Dict[str, str]]: 字典类型列表
        """
        try:
            dict_types = await SysDictType.all().order_by("sort_order")
            
            result = []
            for dict_type in dict_types:
                result.append({
                    'id': str(dict_type.id),
                    'type_name': dict_type.type_name,
                    'type_code': dict_type.type_code,
                    'is_enabled': dict_type.is_enabled,
                    'remark': dict_type.remark or ''
                })
            
            logger.debug(f"获取所有字典类型成功 - 数量: {len(result)}")
            
            return result
            
        except Exception as e:
            logger.error(f"获取所有字典类型失败: {e}")
            return []
    
    async def refresh_cache(self, dict_type_code: str = None):
        """刷新字典缓存
        
        Args:
            dict_type_code: 字典类型代码，如果为None则刷新所有缓存
        """
        if dict_type_code:
            self.clear_cache(dict_type_code)
            await self.get_dict_values(dict_type_code)
            logger.debug(f"刷新字典缓存 - 类型: {dict_type_code}")
        else:
            # 获取所有字典类型
            dict_types = await SysDictType.all().values_list('type_code', flat=True)
            
            self.clear_cache()
            
            for type_code in dict_types:
                await self.get_dict_values(type_code)
            
            logger.debug("刷新所有字典缓存")