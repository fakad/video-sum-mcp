#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Service Container - 依赖注入容器
提供类型安全的服务注册、解析和生命周期管理
"""

import asyncio
from typing import TypeVar, Type, Dict, Any, Optional, Callable, Union, List
from abc import ABC, abstractmethod
import threading
from contextlib import contextmanager
import logging

from ..interfaces import IServiceContainer

logger = logging.getLogger(__name__)

T = TypeVar('T')

class ServiceLifetime:
    """服务生命周期枚举"""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"

class ServiceDescriptor:
    """服务描述符"""
    def __init__(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None,
        instance: Optional[T] = None,
        lifetime: str = ServiceLifetime.SINGLETON
    ):
        self.service_type = service_type
        self.implementation_type = implementation_type
        self.factory = factory
        self.instance = instance
        self.lifetime = lifetime
        
        # 验证配置
        provided_options = sum([
            implementation_type is not None,
            factory is not None,
            instance is not None
        ])
        
        if provided_options != 1:
            raise ValueError("Must provide exactly one of: implementation_type, factory, or instance")

class ServiceContainer(IServiceContainer):
    """
    依赖注入服务容器
    支持类型安全的服务注册、解析和生命周期管理
    """
    
    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._scoped_services: Dict[str, Dict[Type, Any]] = {}
        self._current_scope: Optional[str] = None
        self._lock = threading.RLock()
        self._scope_counter = 0
    
    def register_singleton(
        self, 
        service_type: Type[T], 
        implementation_type: Type[T]
    ) -> 'ServiceContainer':
        """注册单例服务"""
        return self._register_service(
            service_type, 
            ServiceDescriptor(
                service_type=service_type,
                implementation_type=implementation_type,
                lifetime=ServiceLifetime.SINGLETON
            )
        )
    
    def register_transient(
        self, 
        service_type: Type[T], 
        implementation_type: Type[T]
    ) -> 'ServiceContainer':
        """注册瞬态服务"""
        return self._register_service(
            service_type,
            ServiceDescriptor(
                service_type=service_type,
                implementation_type=implementation_type,
                lifetime=ServiceLifetime.TRANSIENT
            )
        )
    
    def register_scoped(
        self, 
        service_type: Type[T], 
        implementation_type: Type[T]
    ) -> 'ServiceContainer':
        """注册作用域服务"""
        return self._register_service(
            service_type,
            ServiceDescriptor(
                service_type=service_type,
                implementation_type=implementation_type,
                lifetime=ServiceLifetime.SCOPED
            )
        )
    
    def register_instance(
        self, 
        service_type: Type[T], 
        instance: T
    ) -> 'ServiceContainer':
        """注册服务实例"""
        return self._register_service(
            service_type,
            ServiceDescriptor(
                service_type=service_type,
                instance=instance,
                lifetime=ServiceLifetime.SINGLETON
            )
        )
    
    def register_factory(
        self, 
        service_type: Type[T], 
        factory: Callable[[], T],
        lifetime: str = ServiceLifetime.SINGLETON
    ) -> 'ServiceContainer':
        """注册工厂方法"""
        return self._register_service(
            service_type,
            ServiceDescriptor(
                service_type=service_type,
                factory=factory,
                lifetime=lifetime
            )
        )
    
    def _register_service(
        self, 
        service_type: Type[T], 
        descriptor: ServiceDescriptor
    ) -> 'ServiceContainer':
        """内部服务注册方法"""
        with self._lock:
            self._services[service_type] = descriptor
            logger.debug(f"Registered service {service_type.__name__} with lifetime {descriptor.lifetime}")
        return self
    
    def get_service(self, service_type: Type[T]) -> T:
        """获取服务实例"""
        with self._lock:
            if service_type not in self._services:
                raise ValueError(f"Service {service_type.__name__} not registered")
            
            descriptor = self._services[service_type]
            
            # 处理已有实例
            if descriptor.instance is not None:
                return descriptor.instance
            
            # 处理单例
            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                if service_type in self._singletons:
                    return self._singletons[service_type]
                
                instance = self._create_instance(descriptor)
                self._singletons[service_type] = instance
                return instance
            
            # 处理作用域服务
            elif descriptor.lifetime == ServiceLifetime.SCOPED:
                if self._current_scope is None:
                    raise RuntimeError("No active scope for scoped service")
                
                scope_services = self._scoped_services.get(self._current_scope, {})
                if service_type in scope_services:
                    return scope_services[service_type]
                
                instance = self._create_instance(descriptor)
                if self._current_scope not in self._scoped_services:
                    self._scoped_services[self._current_scope] = {}
                self._scoped_services[self._current_scope][service_type] = instance
                return instance
            
            # 处理瞬态服务
            else:  # TRANSIENT
                return self._create_instance(descriptor)
    
    def _create_instance(self, descriptor: ServiceDescriptor):
        """创建服务实例"""
        try:
            if descriptor.factory:
                return descriptor.factory()
            elif descriptor.implementation_type:
                return self._instantiate_type(descriptor.implementation_type)
            else:
                raise ValueError("No way to create instance for descriptor")
        except Exception as e:
            logger.error(f"Failed to create instance for {descriptor.service_type.__name__}: {e}")
            raise
    
    def _instantiate_type(self, impl_type: Type[T]) -> T:
        """实例化类型，支持构造函数依赖注入"""
        try:
            # 尝试无参构造
            return impl_type()
        except TypeError:
            # 如果需要依赖注入，可以在这里扩展
            # 目前简单处理，实际项目中可能需要更复杂的依赖解析
            logger.warning(f"Constructor injection not yet supported for {impl_type.__name__}")
            raise
    
    @contextmanager
    def create_scope(self):
        """创建服务作用域"""
        scope_id = f"scope_{self._scope_counter}"
        self._scope_counter += 1
        
        old_scope = self._current_scope
        self._current_scope = scope_id
        
        try:
            logger.debug(f"Created scope {scope_id}")
            yield self
        finally:
            # 清理作用域服务
            if scope_id in self._scoped_services:
                del self._scoped_services[scope_id]
            self._current_scope = old_scope
            logger.debug(f"Disposed scope {scope_id}")
    
    def is_registered(self, service_type: Type[T]) -> bool:
        """检查服务是否已注册"""
        return service_type in self._services
    
    def get_registered_services(self) -> List[Type]:
        """获取所有已注册的服务类型"""
        return list(self._services.keys())
    
    def clear(self):
        """清理所有服务"""
        with self._lock:
            self._services.clear()
            self._singletons.clear()
            self._scoped_services.clear()
            self._current_scope = None
            logger.debug("Service container cleared")

# 全局服务容器实例
_global_container: Optional[ServiceContainer] = None
_container_lock = threading.Lock()

def get_global_container() -> ServiceContainer:
    """获取全局服务容器"""
    global _global_container
    if _global_container is None:
        with _container_lock:
            if _global_container is None:
                _global_container = ServiceContainer()
    return _global_container

def set_global_container(container: ServiceContainer):
    """设置全局服务容器"""
    global _global_container
    with _container_lock:
        _global_container = container

def clear_global_container():
    """清理全局服务容器"""
    global _global_container
    with _container_lock:
        if _global_container:
            _global_container.clear()
        _global_container = None 