#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI服务包
包含所有AI相关的服务实现
"""

__version__ = "0.1.0"
__author__ = "DeviceMonitor Team"

# 导入各个服务
from app.services.ai.trainer import BaseTrainer
from app.services.ai.data_loader import TDengineLoader
