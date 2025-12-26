#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI模块延迟加载器"""

import importlib
from typing import Dict, Any, List
from loguru import logger

from app.settings.ai_settings import ai_settings


class AIModuleLoader:
    """AI模块延迟加载器"""
    
    def __init__(self):
        self._loaded = False
        self._services = {}
        self._routers = []
        self._dependencies_checked = False
    
    def is_enabled(self) -> bool:
        """检查AI模块是否启用"""
        return ai_settings.ai_module_enabled
    
    def is_loaded(self) -> bool:
        """检查AI模块是否已加载"""
        return self._loaded
    
    def load_module(self) -> bool:
        """加载AI模块"""
        if self._loaded:
            logger.warning("AI模块已加载，跳过")
            return True
        
        if not self.is_enabled():
            logger.info("⏸️ AI模块未启用，跳过加载")
            return False
        
        try:
            logger.info("🚀 开始加载AI模块...")
            
            # 检查依赖
            self._check_dependencies()
            
            # 注册AI服务
            self._register_services()
            
            # 注册AI路由
            self._register_routers()
            
            self._loaded = True
            logger.info("✅ AI模块加载成功")
            
            # 打印启用的功能
            enabled_features = []
            if ai_settings.ai_feature_extraction_enabled:
                enabled_features.append('特征提取')
            if ai_settings.ai_anomaly_detection_enabled:
                enabled_features.append('异常检测')
            if ai_settings.ai_trend_prediction_enabled:
                enabled_features.append('趋势预测')
            if ai_settings.ai_health_scoring_enabled:
                enabled_features.append('健康评分')
            if ai_settings.ai_smart_analysis_enabled:
                enabled_features.append('智能分析')
            
            if enabled_features:
                logger.info(f"启用的AI功能: {', '.join(enabled_features)}")
            else:
                logger.warning("⚠️ AI模块启用但无具体功能启用，请检查配置")
            
            return True
        
        except Exception as e:
            logger.error(f"❌ AI模块加载失败: {str(e)}")
            logger.exception(e)
            return False
    
    def _check_dependencies(self):
        """检查AI模块依赖"""
        if self._dependencies_checked:
            return
        
        logger.info("检查AI模块依赖...")
        missing_deps = []
        required_libs = set()
        
        # 根据启用的功能收集所需的依赖
        if ai_settings.ai_feature_extraction_enabled:
            required_libs.update(['numpy', 'pandas'])
            logger.debug("特征提取启用，需要: numpy, pandas")
        
        if ai_settings.ai_anomaly_detection_enabled or \
           ai_settings.ai_trend_prediction_enabled:
            required_libs.update(['sklearn', 'numpy', 'scipy'])
            logger.debug("异常检测/趋势预测启用，需要: sklearn, numpy, scipy")
        
        if ai_settings.ai_health_scoring_enabled:
            required_libs.add('numpy')
            logger.debug("健康评分启用，需要: numpy")
        
        # 检查每个依赖
        for lib in required_libs:
            try:
                # 尝试导入库
                importlib.import_module(lib)
                logger.debug(f"✓ {lib} 已安装")
            except ImportError:
                missing_deps.append(lib)
                logger.warning(f"✗ {lib} 未安装")
        
        if missing_deps:
            # 提供友好的错误信息
            error_msg = (
                f"缺少AI模块依赖: {', '.join(missing_deps)}\n"
                f"请运行: pip install {' '.join(missing_deps)}\n"
                f"或暂时禁用相关功能"
            )
            logger.error(f"❌ {error_msg}")
            raise ImportError(error_msg)
        
        self._dependencies_checked = True
        logger.info(f"✅ AI依赖检查通过 (检查了 {len(required_libs)} 个库)")
    
    def _register_services(self):
        """注册AI服务"""
        logger.info("注册AI服务...")
        # TODO: Phase 4 实现服务注册
        # 例如:
        # from app.services.ai.feature_extraction import AIFeatureExtractionService
        # self._services['feature_extraction'] = AIFeatureExtractionService()
        logger.info("✅ AI服务注册完成 (当前为占位符)")
    
    def _register_routers(self):
        """注册AI路由"""
        logger.info("注册AI路由...")
        
        try:
            # 导入AI总路由（已在 __init__.py 中根据配置条件导入子路由）
            from app.api.v2.ai import ai_router
            self._routers.append(ai_router)
            logger.info("✅ AI路由注册完成")
        except ImportError as e:
            logger.error(f"❌ 导入AI路由失败: {e}")
            raise
    
    def get_routers(self) -> List:
        """获取所有AI路由"""
        return self._routers
    
    def unload_module(self):
        """卸载AI模块"""
        if not self._loaded:
            return
        
        logger.info("🗑️ 卸载AI模块...")
        self._services.clear()
        self._routers.clear()
        self._loaded = False
        logger.info("✅ AI模块已卸载")


# 全局加载器实例
ai_loader = AIModuleLoader()

