#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
标准服务接口定义

定义项目中核心服务的协议接口，使用Python的Protocol机制
确保类型安全和接口契约。
"""

from typing import Protocol, Dict, Any, Optional, List
from abc import ABC, abstractmethod


class IExtractor(Protocol):
    """内容提取器接口协议"""
    
    def extract(self, url: str, context_text: str = "") -> Dict[str, Any]:
        """提取内容"""
        ...
    
    def validate_url(self, url: str) -> bool:
        """验证URL是否支持"""
        ...
    
    def get_platform_config(self) -> Dict[str, Any]:
        """获取平台配置"""
        ...


class IFormatter(Protocol):
    """格式化器接口协议"""
    
    def format(self, data: Dict[str, Any], output_file: str) -> Dict[str, Any]:
        """格式化数据到文件"""
        ...


class ICacheManager(Protocol):
    """缓存管理器接口协议"""
    
    def get_cached_result(self, key: str) -> Optional[Dict[str, Any]]:
        """获取缓存结果"""
        ...
    
    def cache_result(self, key: str, result: Dict[str, Any]) -> bool:
        """缓存结果"""
        ...
    
    def clear_cache(self) -> int:
        """清理缓存"""
        ...


class IConfigManager(Protocol):
    """配置管理器接口协议"""
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """获取配置节"""
        ...
    
    def get_platform_config(self, platform: str) -> Dict[str, Any]:
        """获取平台配置"""
        ...
    
    def reload(self) -> bool:
        """重新加载配置"""
        ...


class IPlatformStrategy(Protocol):
    """平台策略接口协议"""
    
    def get_strategy(self, platform: str) -> Any:
        """获取平台策略"""
        ...
    
    def detect_platform(self, url: str) -> str:
        """检测平台类型"""
        ...


class IQualitySupervisor(Protocol):
    """质量监督器接口协议"""
    
    def assess_quality(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """评估质量"""
        ...
    
    def validate_content(self, content: Dict[str, Any]) -> bool:
        """验证内容"""
        ...


# 服务类型定义
ServiceType = str
ServiceInstance = Any
ServiceFactory = callable


class IServiceContainer(Protocol):
    """服务容器接口协议"""
    
    def register_singleton(self, name: ServiceType, instance: ServiceInstance) -> None:
        """注册单例服务"""
        ...
    
    def register_factory(self, name: ServiceType, factory: ServiceFactory) -> None:
        """注册工厂服务"""
        ...
    
    def get(self, name: ServiceType) -> ServiceInstance:
        """获取服务实例"""
        ...
    
    def has(self, name: ServiceType) -> bool:
        """检查服务是否存在"""
        ...
    
    def clear(self) -> None:
        """清空容器"""
        ... 